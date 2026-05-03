from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
import cv2
import numpy as np
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from app.database import get_db
import model.ml_pipeline as ml_pipeline
from app.notifications import send_spoilage_notification
from model.spoilage_predictor import predict_spoilage
from app.config import settings

router = APIRouter()

# Notification logic handled by app.notifications

@router.post("/ingest")
async def ingest_image(
    device_id: str = Form(...),
    timestamp: str = Form(...),
    image: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    # 1. Read and decode image
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
    
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image data")

    if settings.SAVE_UPLOADED_IMAGES:
        save_dir = Path(settings.UPLOAD_SAVE_PATH)
        save_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(image.filename).name}"
        save_path = save_dir / safe_filename
        save_path.write_bytes(contents)
        print(f"[IMAGE SAVED] {save_path}")
    # 2. Extract colors using ML pipeline
    sticker_readings = ml_pipeline.extract_colors(img)

    if settings.SIMULATE_PROGRESS:
        try:
            ts_dt = datetime.fromisoformat(timestamp)
            # Use hours as progression signal
            progress = (ts_dt.hour % 24) / 24.0
        except:
            progress = 0.0

        print(f"[SIMULATION] Progress factor: {progress:.2f}")

        for k in sticker_readings:
            base = sticker_readings[k]["spoilage_score"]
            
            # Controlled increase (NOT full override)
            new_score = min(1.0, base + 0.6 * progress)

            print(f"[SIM] {k}: {base:.3f} → {new_score:.3f}")

            sticker_readings[k]["spoilage_score"] = new_score
            
    if settings.DEBUG_LOGGING:
        print("FINAL SCORES:", {
            k: sticker_readings[k]["spoilage_score"]
            for k in sticker_readings
        })

    # 3. Look up the active food item for this device
    async with db.execute(
        "SELECT item_id, label, food_category FROM food_items WHERE device_id = ? AND is_active = 1 LIMIT 1",
        (device_id,)
    ) as cursor:
        item = await cursor.fetchone()
    
    if not item:
        raise HTTPException(status_code=404, detail="No active food item found for this device")
    
    item_id, label, food_category = item

    # 3b. Insert color readings into database
    for sticker_type, data in sticker_readings.items():
        await db.execute(
            """
            INSERT INTO color_readings (
                item_id, sticker_type, timestamp, 
                R, G, B, H, S, V, L_star, a_star, b_star, spoilage_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id, sticker_type, timestamp,
                data["R"], data["G"], data["B"], data["H"], data["S"], data["V"],
                data["L_star"], data["a_star"], data["b_star"], data["spoilage_score"]
            )
        )
    
    await db.commit()

    # 4. Fetch last 10 color readings for history
    async with db.execute(
        "SELECT * FROM color_readings WHERE item_id = ? ORDER BY timestamp DESC LIMIT 30", # 3 readings per ingest, so 10 ingests = 30 rows
        (item_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        
        grouped = defaultdict(dict)

        for r in rows:
            ts_dt = datetime.fromisoformat(r[3])
            ts = ts_dt.replace(microsecond=0)
            grouped[ts][r[2]] = r[13]

        history = []
        for ts, data in grouped.items():
            if all(k in data for k in ["BCG", "BTB", "KMNO4"]):
                history.append({
                    "timestamp": ts,
                    "BCG_score": data["BCG"],
                    "BTB_score": data["BTB"],
                    "KMNO4_score": data["KMNO4"]
                })

        history.sort(key=lambda x: x["timestamp"])
        print("\n==== DEBUG HISTORY ====")
        print("Raw rows:", len(rows))
        print("Grouped keys:", len(grouped))
        print("Final history:", len(history))

        for h in history:
            print(h)
            
    # 5. Predict spoilage
    prediction_result = predict_spoilage(history, food_category)
    print("Method: ", prediction_result['method'])

    # 6. Insert prediction into database
    now_str = datetime.now().isoformat()
    await db.execute(
        """
        INSERT INTO predictions (item_id, predicted_at, predicted_spoil_by, confidence, method)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            item_id, 
            now_str, 
            prediction_result["predicted_spoil_by"],
            prediction_result["confidence"], 
            prediction_result["method"]
        )
    )
    await db.commit()

    # 7. Check for alert threshold and "send" notification
    # Use max spoilage score from current readings for the alert log
    current_max_spoilage = max(d["spoilage_score"] for d in sticker_readings.values())
    
    if prediction_result["hours_remaining"] < 24:
        await send_spoilage_notification(
            device_id, label, 
            prediction_result["hours_remaining"], 
            item_id, current_max_spoilage,
            db
        )
    
    
    # 8. Return response
    return {
        "status": "ok",
        "prediction": {
            "hours_remaining": prediction_result["hours_remaining"],
            "predicted_spoil_by": prediction_result["predicted_spoil_by"],
            "confidence": prediction_result["confidence"],
            "method": prediction_result["method"]
        }
    }

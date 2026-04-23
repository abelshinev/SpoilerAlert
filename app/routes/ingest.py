from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
import cv2
import numpy as np
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any

from app.database import get_db
from app import ml_pipeline

router = APIRouter()

def send_notification(device_id: str, label: str, hours: float, item_id: int, spoilage_score: float):
    """
    STUB: Placeholder for Firebase push notifications.
    """
    print("\n" + "="*50)
    print(f"PUSH NOTIFICATION SENT TO DEVICE: {device_id}")
    print(f"ALERT: Food item '{label}' (ID: {item_id}) is spoiling!")
    print(f"Estimated time remaining: {hours:.1f} hours")
    print(f"Current Max Spoilage Score: {spoilage_score:.2f}")
    print("="*50 + "\n")

@router.post("")
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

    # 2. Extract colors using ML pipeline
    sticker_readings = ml_pipeline.extract_colors(img)

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
        
        history = []
        for r in rows:
            history.append({
                "sticker_type": r[2],
                "timestamp": r[3],
                "R": r[4], "G": r[5], "B": r[6],
                "H": r[7], "S": r[8], "V": r[9],
                "L_star": r[10], "a_star": r[11], "b_star": r[12],
                "spoilage_score": r[13]
            })

    # 5. Predict spoilage
    prediction_result = ml_pipeline.predict_spoilage(history, food_category)

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
            prediction_result["predicted_spoil_by"].isoformat(),
            prediction_result["confidence"], 
            prediction_result["method"]
        )
    )
    await db.commit()

    # 7. Check for alert threshold and "send" notification
    # Use max spoilage score from current readings for the alert log
    current_max_spoilage = max(d["spoilage_score"] for d in sticker_readings.values())
    
    if prediction_result["hours_remaining"] < 24:
        send_notification(
            device_id, label, 
            prediction_result["hours_remaining"], 
            item_id, current_max_spoilage
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

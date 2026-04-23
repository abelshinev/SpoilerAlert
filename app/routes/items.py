from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import aiosqlite
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.database import get_db

router = APIRouter()

class AddFoodItem(BaseModel):
    device_id: str
    label: str
    food_category: str

VALID_CATEGORIES = ["raw_meat", "dairy", "leafy", "cooked"]

@router.post("/add-food-item")
async def add_food_item(data: AddFoodItem, db: aiosqlite.Connection = Depends(get_db)):
    if data.food_category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid food_category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    # Generate item_id as UUID
    item_id = str(uuid.uuid4())
    
    await db.execute(
        """
        INSERT INTO food_items (item_id, device_id, label, food_category, placed_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (item_id, data.device_id, data.label, data.food_category, datetime.now().isoformat(), 1)
    )
    await db.commit()
    
    return {"status": "created", "item_id": item_id}

@router.get("/{device_id}")
async def get_items(device_id: str, db: aiosqlite.Connection = Depends(get_db)):
    # 1. Fetch active items for the device
    async with db.execute(
        "SELECT * FROM food_items WHERE device_id = ? AND is_active = 1",
        (device_id,)
    ) as cursor:
        items = await cursor.fetchall()
    
    result = []
    for item in items:
        item_dict = dict(item)
        item_id = item_dict["item_id"]
        
        # 2. Get latest prediction for this item
        async with db.execute(
            """
            SELECT predicted_spoil_by, confidence, method 
            FROM predictions 
            WHERE item_id = ? 
            ORDER BY predicted_at DESC LIMIT 1
            """,
            (item_id,)
        ) as pred_cursor:
            pred = await pred_cursor.fetchone()
        
        latest_prediction = None
        if pred:
            pred_dict = dict(pred)
            # Calculate hours_remaining for the response (optional but requested in shape)
            # We'll use the predicted_spoil_by and current time if needed, 
            # or just return the fields from DB.
            # The prompt requested: { predicted_spoil_by, hours_remaining, confidence, method }
            # hours_remaining wasn't in the predictions table explicitly, but we can calculate it.
            try:
                spoil_dt = datetime.fromisoformat(pred_dict["predicted_spoil_by"])
                hours_left = (spoil_dt - datetime.now()).total_seconds() / 3600.0
            except:
                hours_left = 0.0

            latest_prediction = {
                "predicted_spoil_by": pred_dict["predicted_spoil_by"],
                "hours_remaining": max(0, hours_left),
                "confidence": pred_dict["confidence"],
                "method": pred_dict["method"]
            }
        
        item_dict["latest_prediction"] = latest_prediction
        result.append(item_dict)
    
    return result

@router.get("/item-history/{item_id}")
async def get_item_history(item_id: str, db: aiosqlite.Connection = Depends(get_db)):
    # 1. Fetch all color readings ASC
    async with db.execute(
        "SELECT * FROM color_readings WHERE item_id = ? ORDER BY timestamp ASC",
        (item_id,)
    ) as cursor:
        readings = await cursor.fetchall()
    
    # 2. Fetch all predictions ASC
    async with db.execute(
        "SELECT * FROM predictions WHERE item_id = ? ORDER BY predicted_at ASC",
        (item_id,)
    ) as cursor:
        predictions = await cursor.fetchall()
        
    return {
        "item_id": item_id,
        "color_readings": [dict(r) for r in readings],
        "predictions": [dict(r) for r in predictions]
    }

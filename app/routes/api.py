from fastapi import APIRouter
from datetime import datetime
import random
from app.database import get_db
from fastapi import Depends
import aiosqlite


user_settings = {
    "alert_level": "Spoiling",
    "alert_timing": "1 day before",
    "alert_frequency": "Daily",
    "update_frequency_hours": 6
}

router = APIRouter(prefix="/api", tags=["api"])
latest_ml_data = None
history = []

@router.get("/esp-config")
def get_esp_config():
    global user_settings

    return {
        "capture_interval_hours": int(user_settings["update_frequency_hours"])
    }

@router.get("/settings")
def get_settings():
    global user_settings
    return user_settings

@router.put("/settings")
def update_settings(data: dict):
    global user_settings

    user_settings["alert_level"] = data.get("alert_level", user_settings["alert_level"])
    user_settings["alert_timing"] = data.get("alert_timing", user_settings["alert_timing"])
    user_settings["alert_frequency"] = data.get("alert_frequency", user_settings["alert_frequency"])
    user_settings["update_frequency_hours"] = data.get(
        "update_frequency_hours",
        user_settings["update_frequency_hours"]
    )

    return user_settings


@router.get("/status")
async def get_status(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT predicted_spoil_by, confidence, method FROM predictions ORDER BY predicted_at DESC LIMIT 1"
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        return {"status": "Fresh", "confidence": 0.9}

    predicted_spoil_by, confidence, method = row

    # compute hours remaining
    spoil_time = datetime.fromisoformat(predicted_spoil_by)
    hours_remaining = (spoil_time - datetime.now()).total_seconds() / 3600

    if hours_remaining > 24:
        status = "Fresh"
    elif hours_remaining > 6:
        status = "Spoiling"
    else:
        status = "Spoiled"

    return {
        "status": status,
        "confidence": confidence,
        "hours_remaining": round(hours_remaining, 2)
    }

@router.get("/trend")
async def get_trend(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT predicted_at, predicted_spoil_by FROM predictions ORDER BY predicted_at DESC LIMIT 7"
    ) as cursor:
        rows = await cursor.fetchall()

    rows.reverse()
    points = []

    for r in rows:
        predicted_at, predicted_spoil_by = r

        spoil_time = datetime.fromisoformat(predicted_spoil_by)
        pred_time = datetime.fromisoformat(predicted_at)

        hours_remaining = (spoil_time - datetime.now()).total_seconds() / 3600

        if hours_remaining > 24:
            value = 0
        elif hours_remaining > 6:
            value = 2
        else:
            value = 4

        points.append({
            "day": datetime.fromisoformat(predicted_at).strftime("%a"),
            "value": value
        })

    return {"points": points}

@router.get("/notifications")
def get_notifications():
    return {
        "notifications": [
            {
                "id": "1",
                "title": "Reminder",
                "message": "Check your vegetables",
                "type": "warning",
                "timestamp": str(datetime.now())
            }
        ]
    }


@router.get("/device-status")
def get_device_status():
    return {
        "is_online": True,
        "last_seen": str(datetime.now())
    }

@router.post("/ml-update")
def update_from_ml(data: dict):
    global latest_ml_data, history

    hours_remaining = data.get("hours_remaining", 0)

    # 🔹 Determine status
    if hours_remaining > 24:
        status = "Fresh"
        value = 0
    elif hours_remaining > 6:
        status = "Spoiling"
        value = 2
    else:
        status = "Spoiled"
        value = 4

    # 🔹 Update latest status
    latest_ml_data = {
        "status": status,
        "confidence": data.get("confidence", 0.0),
        "timestamp": str(datetime.now())
    }

    # 🔹 Update history
    history.append({
        "day": datetime.now().strftime("%a"),
        "value": value
    })

    history = history[-7:]  # keep last 7 points

    return {"message": "ML data updated"}
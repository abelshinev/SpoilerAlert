from fastapi import APIRouter
from datetime import datetime
import random

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
def get_status():
    if latest_ml_data:
        return latest_ml_data

    return {
        "status": "Fresh",
        "confidence": 0.9
    }


@router.get("/trend")
def get_trend():
    global history

    # 🔹 Ensure history is always a list
    if not isinstance(history, list):
        history = []

    # 🔹 If empty, return safe empty structure
    if len(history) == 0:
        return {
            "points": []
        }

    # 🔹 Keep only last 7 entries (weekly view)
    trimmed = history[-7:]

    # 🔹 Ensure each point has correct format
    safe_points = []
    for point in trimmed:
        try:
            safe_points.append({
                "day": str(point.get("day", "")),
                "value": int(point.get("value", 0))
            })
        except Exception:
            # fallback in case of bad data
            safe_points.append({
                "day": "N/A",
                "value": 0
            })

    return {
        "points": safe_points
    }

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
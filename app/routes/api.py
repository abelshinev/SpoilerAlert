from fastapi import APIRouter
from datetime import datetime
import random

router = APIRouter(prefix="/api", tags=["api"])


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
    if history:
        return {"points": history}

    return {
        "points": [
            {"day": "Mon", "value": 1},
            {"day": "Tue", "value": 2},
        ]
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

    # Apply your rule
    if hours_remaining > 24:
        status = "Fresh"
        value = 0
    elif hours_remaining > 6:
        status = "Spoiling"
        value = 2
    else:
        status = "Spoiled"
        value = 4

    latest_ml_data = {
        "status": status,
        "confidence": data.get("confidence", 0.0),
        "timestamp": str(datetime.now())
    }

    # Save for graph (last 7 points)
    history.append({
        "day": datetime.now().strftime("%a"),
        "value": value
    })

    history = history[-7:]  # keep last 7

    return {"message": "ML data updated"}
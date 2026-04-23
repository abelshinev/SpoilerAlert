from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import aiosqlite
from datetime import datetime
from app.database import get_db

router = APIRouter()

class DeviceRegister(BaseModel):
    device_id: str
    user_id: str

class FCMTokenUpdate(BaseModel):
    device_id: str
    fcm_token: str

@router.post("/register-device")
async def register_device(data: DeviceRegister, db: aiosqlite.Connection = Depends(get_db)):
    # Check if exists
    async with db.execute("SELECT 1 FROM devices WHERE device_id = ?", (data.device_id,)) as cursor:
        if await cursor.fetchone():
            raise HTTPException(status_code=409, detail="Device already registered")
    
    await db.execute(
        "INSERT INTO devices (device_id, user_id, fcm_token, registered_at) VALUES (?, ?, ?, ?)",
        (data.device_id, data.user_id, None, datetime.now().isoformat())
    )
    await db.commit()
    return {"status": "registered", "device_id": data.device_id}

@router.post("/register-fcm-token")
async def register_fcm_token(data: FCMTokenUpdate, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT 1 FROM devices WHERE device_id = ?", (data.device_id,)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Device not found")
    
    await db.execute(
        "UPDATE devices SET fcm_token = ? WHERE device_id = ?",
        (data.fcm_token, data.device_id)
    )
    await db.commit()
    return {"status": "updated"}

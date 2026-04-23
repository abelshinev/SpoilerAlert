from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Device:
    device_id: str
    user_id: str
    fcm_token: str
    registered_at: datetime

@dataclass
class FoodItem:
    item_id: Optional[int]
    device_id: str
    label: str
    food_category: str  # raw_meat | dairy | leafy | cooked
    placed_at: datetime
    is_active: bool = True

@dataclass
class ColorReading:
    id: Optional[int]
    item_id: int
    sticker_type: str
    timestamp: datetime
    R: float
    G: float
    B: float
    H: float
    S: float
    V: float
    L_star: float
    a_star: float
    b_star: float
    spoilage_score: float

@dataclass
class Prediction:
    id: Optional[int]
    item_id: int
    predicted_at: datetime
    predicted_spoil_by: datetime
    confidence: float
    method: str

@dataclass
class Feedback:
    id: Optional[int]
    item_id: int
    submitted_at: datetime
    actual_spoil_at: datetime
    predicted_spoil_at: datetime
    error_hours: float

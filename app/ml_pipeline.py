# STUB: Replace with real ML module import before production
import numpy as np
import random
from datetime import datetime, timedelta

def extract_colors(image: np.ndarray) -> dict:
    """
    STUB: Extract color readings from image for three sensor types.
    Returns realistic-looking mock values with small random variations.
    """
    def get_mock_data():
        return {
            "R": 150.0 + random.uniform(-10, 10),
            "G": 100.0 + random.uniform(-10, 10),
            "B": 50.0 + random.uniform(-10, 10),
            "H": 0.12 + random.uniform(-0.02, 0.02),
            "S": 0.45 + random.uniform(-0.05, 0.05),
            "V": 0.78 + random.uniform(-0.05, 0.05),
            "L_star": 45.2 + random.uniform(-2.0, 2.0),
            "a_star": 12.5 + random.uniform(-1.5, 1.5),
            "b_star": 24.8 + random.uniform(-1.5, 1.5),
            "spoilage_score": random.uniform(0.05, 0.25)
        }

    return {
        "BCG": get_mock_data(),
        "BTB": get_mock_data(),
        "KMNO4": get_mock_data()
    }

def predict_spoilage(readings: list[dict], food_category: str) -> dict:
    """
    STUB: Predict spoilage time based on historical color readings and food category.
    Returns fixed stub values as requested.
    """
    hours_remaining = 30.0
    now = datetime.now()
    predicted_spoil_by = now + timedelta(hours=hours_remaining)

    return {
        "predicted_spoil_by": predicted_spoil_by,
        "hours_remaining": hours_remaining,
        "confidence": 0.85,
        "method": "rule_based"
    }

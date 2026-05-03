import numpy as np
from scipy.stats import linregress
import joblib
import json
import os
from datetime import datetime, timedelta

SHELF_LIVES = {
    "raw_meat": 48, "dairy": 144, "leafy": 96, "cooked": 84
}
WEIGHTS = {
    "raw_meat": {"BCG": 0.20, "BTB": 0.60, "KMNO4": 0.20},
    "dairy":    {"BCG": 0.50, "BTB": 0.30, "KMNO4": 0.20},
    "leafy":    {"BCG": 0.30, "BTB": 0.20, "KMNO4": 0.50},
    "cooked":   {"BCG": 0.33, "BTB": 0.33, "KMNO4": 0.34},
}
CAT_ENCODE = {"raw_meat": 0, "dairy": 1, "leafy": 2, "cooked": 3}
RETRAIN_THRESHOLD = 5
FEEDBACK_STORE    = "feedback_store.json"
MODEL_PATH        = "spoilage_model.pkl"
SCALER_PATH       = "scaler.pkl"

def _load_artifacts():
    m = None
    s = None
    for path in [MODEL_PATH, os.path.join("spoiler_alert", MODEL_PATH)]:
        if os.path.exists(path):
            m = joblib.load(path)
            break
            
    for path in [SCALER_PATH, os.path.join("spoiler_alert", SCALER_PATH)]:
        if os.path.exists(path):
            s = joblib.load(path)
            break
            
    print(f"Model loaded: {m is not None}")
    print(f"Scaler loaded: {s is not None}")
    return m, s

model, scaler = _load_artifacts()

def _compute_weighted_score(reading: dict, food_category: str) -> float:
    w = WEIGHTS[food_category]
    return (reading.get("BCG_score", 0.0) * w["BCG"] + 
            reading.get("BTB_score", 0.0) * w["BTB"] + 
            reading.get("KMNO4_score", 0.0) * w["KMNO4"])

def _extract_features(readings: list[dict], food_category: str) -> dict | None:
    if len(readings) < 3:
        return None
        
    t0 = readings[0]["timestamp"]
    t_end = readings[-1]["timestamp"]
    hours_elapsed = (t_end - t0).total_seconds() / 3600.0
    
    current_score = _compute_weighted_score(readings[-1], food_category)
    
    rates = []
    times_for_rates = []
    for i in range(1, len(readings)):
        prev = readings[i-1]
        curr = readings[i]
        
        prev_score = _compute_weighted_score(prev, food_category)
        curr_score = _compute_weighted_score(curr, food_category)
        
        score_diff = curr_score - prev_score
        time_diff = (curr["timestamp"] - prev["timestamp"]).total_seconds() / 3600.0
        
        rate = score_diff / time_diff if time_diff > 0 else 0
        rates.append(rate)
        times_for_rates.append((curr["timestamp"] - t0).total_seconds() / 3600.0)
        
    mean_rate = float(np.mean(rates))
    max_rate = float(np.max(rates))
    
    if len(rates) > 1:
        slope, _, _, _, _ = linregress(times_for_rates, rates)
        rate_trend = float(slope) if not np.isnan(slope) else 0.0
    else:
        rate_trend = 0.0
        
    bcg_score = readings[-1].get("BCG_score", 0.0)
    btb_score = readings[-1].get("BTB_score", 0.0)
    kmno4_score = readings[-1].get("KMNO4_score", 0.0)
    
    scores = [bcg_score, btb_score, kmno4_score]
    dominant_sticker = int(np.argmax(scores))
    
    food_cat = CAT_ENCODE[food_category]
    
    return {
        "hours_elapsed": hours_elapsed,
        "current_score": current_score,
        "mean_rate": mean_rate,
        "max_rate": max_rate,
        "rate_trend": rate_trend,
        "bcg_score": bcg_score,
        "btb_score": btb_score,
        "kmno4_score": kmno4_score,
        "dominant_sticker": dominant_sticker,
        "food_category": food_cat
    }

def _layer1_predict(readings: list[dict], food_category: str) -> float:
    latest = readings[-1]
    weighted_score = _compute_weighted_score(latest, food_category)
    
    temp_scale_factor = 1.0
    for path in ["score_config.json", os.path.join("..", "score_config.json")]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    config = json.load(f)
                    temp_scale_factor = config.get("temp_scale_factor", 1.0)
                break
            except Exception:
                pass
                
    shelf_life = SHELF_LIVES[food_category] * temp_scale_factor
    hours_remaining = shelf_life * (1 - weighted_score)
    return max(0.0, float(hours_remaining))

def _layer2_predict(readings: list[dict], food_category: str) -> float:
    features = _extract_features(readings, food_category)
    if features is None or model is None or scaler is None:
        return _layer1_predict(readings, food_category)
        
    feature_list = [
        features["hours_elapsed"], features["current_score"],
        features["mean_rate"], features["max_rate"], features["rate_trend"],
        features["bcg_score"], features["btb_score"], features["kmno4_score"],
        features["dominant_sticker"], features["food_category"]
    ]
    
    X_scaled = scaler.transform([feature_list])
    hours_remaining = model.predict(X_scaled)[0]
    return max(0.0, float(hours_remaining))

def predict_spoilage(readings: list[dict], food_category: str) -> dict:
    n = len(readings)
    if n < 3 or model is None:
        method = "rule_based"
        confidence = 0.3
        hours_remaining = _layer1_predict(readings, food_category)
    elif n <= 6:
        method = "curve_fit"
        confidence = 0.6
        hours_remaining = _layer2_predict(readings, food_category)
    else:
        method = "regression"
        confidence = 0.85
        hours_remaining = _layer2_predict(readings, food_category)

    hours_remaining = max(0.0, float(hours_remaining))
    predicted_spoil_by = readings[-1]["timestamp"] + timedelta(hours=hours_remaining)

    return {
        "predicted_spoil_by": predicted_spoil_by.isoformat(),
        "hours_remaining": round(hours_remaining, 2),
        "confidence": confidence,
        "method": method
    }

def retrain_on_feedback(item_id: str, actual_spoil_at: datetime, readings: list[dict], food_category: str) -> None:
    global model
    
    store_path = FEEDBACK_STORE
    if not os.path.exists(store_path) and os.path.exists("spoiler_alert"):
        store_path = os.path.join("spoiler_alert", FEEDBACK_STORE)
        
    if os.path.exists(store_path):
        with open(store_path, "r") as f:
            store = json.load(f)
    else:
        store = []
        
    features = _extract_features(readings, food_category)
    if features is None:
        return
        
    actual_hours = (actual_spoil_at - readings[0]["timestamp"]).total_seconds() / 3600.0
    
    store.append({
        "item_id": item_id,
        "features": features,
        "label": actual_hours
    })
    
    with open(store_path, "w") as f:
        json.dump(store, f, indent=2)
        
    if len(store) % RETRAIN_THRESHOLD == 0 and model is not None and scaler is not None:
        last_entries = store[-RETRAIN_THRESHOLD:]
        
        X = []
        y = []
        for entry in last_entries:
            f_dict = entry["features"]
            feature_list = [
                f_dict["hours_elapsed"], f_dict["current_score"],
                f_dict["mean_rate"], f_dict["max_rate"], f_dict["rate_trend"],
                f_dict["bcg_score"], f_dict["btb_score"], f_dict["kmno4_score"],
                f_dict["dominant_sticker"], f_dict["food_category"]
            ]
            X.append(feature_list)
            y.append(entry["label"])
            
        X_scaled = scaler.transform(X)
        model.partial_fit(X_scaled, y)
        
        m_path = MODEL_PATH
        if not os.path.exists(m_path) and os.path.exists(os.path.join("spoiler_alert", MODEL_PATH)):
            m_path = os.path.join("spoiler_alert", MODEL_PATH)
            
        joblib.dump(model, m_path)
        model = joblib.load(m_path)
        print(f"Model retrained on {len(store)} total feedback samples.")

from model.color_extractor import extract_colors
from model.spoilage_predictor import predict_spoilage, retrain_on_feedback

__all__ = ["extract_colors", "predict_spoilage", "retrain_on_feedback"]

def pipeline_status() -> dict:
    """
    Returns status of all pipeline components.
    """
    import os
    import joblib
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(BASE_DIR, "spoilage_model.pkl")
    config_path = os.path.join(BASE_DIR, "sticker_config.json")
    scaler_path = os.path.join(BASE_DIR, "scaler.pkl")
    
    status = {
        "model_loaded": os.path.exists(model_path),
        "config_loaded": os.path.exists(config_path),
        "scaler_loaded": os.path.exists(scaler_path),
    }
    return status

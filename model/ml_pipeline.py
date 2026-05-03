from color_extractor import extract_colors
from spoilage_predictor import predict_spoilage, retrain_on_feedback

__all__ = ["extract_colors", "predict_spoilage", "retrain_on_feedback"]

def pipeline_status() -> dict:
    """
    Returns status of all pipeline components.
    """
    import os
    import joblib
    
    status = {
        "model_loaded": os.path.exists("spoiler_alert/spoilage_model.pkl") or os.path.exists("spoilage_model.pkl"),
        "config_loaded": os.path.exists("sticker_config.json") or os.path.exists("spoiler_alert/sticker_config.json"),
        "scaler_loaded": os.path.exists("spoiler_alert/scaler.pkl") or os.path.exists("scaler.pkl"),
    }
    return status

import cv2
import numpy as np
import json
import sys
import os

# --- CONSTANTS AND CONFIG LOADING ---

# Default values
BCG_HUE_FRESH = 75
BCG_HUE_SPOILED = 215
BTB_HUE_FRESH = 220
BTB_HUE_SPOILED = 55
KMNO4_HUE_FRESH = 310      # magenta (fresh)
KMNO4_HUE_SPOILED = 25     # brown (spoiled)
BORDER_TRIM = 5

# Attempt to load score_config.json from current directory or parent directory
def load_score_config():
    paths = ["score_config.json", os.path.join("..", "score_config.json")]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
    return None

SCORE_CONFIG = load_score_config()

if SCORE_CONFIG:
    BCG_HUE_FRESH = SCORE_CONFIG.get("BCG", {}).get("hue_fresh", BCG_HUE_FRESH)
    BCG_HUE_SPOILED = SCORE_CONFIG.get("BCG", {}).get("hue_spoiled", BCG_HUE_SPOILED)
    BTB_HUE_FRESH = SCORE_CONFIG.get("BTB", {}).get("hue_fresh", BTB_HUE_FRESH)
    BTB_HUE_SPOILED = SCORE_CONFIG.get("BTB", {}).get("hue_spoiled", BTB_HUE_SPOILED)
    KMNO4_HUE_FRESH = SCORE_CONFIG.get("KMNO4", {}).get("hue_fresh", KMNO4_HUE_FRESH)
    KMNO4_HUE_SPOILED = SCORE_CONFIG.get("KMNO4", {}).get("hue_spoiled", KMNO4_HUE_SPOILED)

def get_status(score):
    if score < 0.3:
        return "FRESH"
    elif score <= 0.7:
        return "SPOILING"
    else:
        return "SPOILED"

# --- CORE FUNCTION ---

def extract_colors(image: np.ndarray) -> dict:
    """
    Crops sticker ROIs, extracts median color features, and computes spoilage scores.
    """
    # Load sticker_config.json
    sticker_config = None
    sticker_paths = ["sticker_config.json", os.path.join("..", "sticker_config.json")]
    for path in sticker_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    sticker_config = json.load(f)
                    break
            except Exception:
                pass
    
    if not sticker_config:
        return {}

    results = {}

    for name in ["KMNO4", "BCG", "BTB"]:
        if name not in sticker_config:
            continue
            
        cfg = sticker_config[name]
        x1, y1, x2, y2 = cfg["x1"], cfg["y1"], cfg["x2"], cfg["y2"]

        # 1. Crop ROI
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        # 2. Trim BORDER_TRIM pixels
        h, w = roi.shape[:2]
        t = BORDER_TRIM
        if h > 2*t and w > 2*t:
            roi_trimmed = roi[t:h-t, t:w-t]
        else:
            roi_trimmed = roi  # Too small to trim

        # 3. Convert to HSV and LAB
        hsv_roi = cv2.cvtColor(roi_trimmed, cv2.COLOR_BGR2HSV)
        lab_roi = cv2.cvtColor(roi_trimmed, cv2.COLOR_BGR2Lab)

        # 4. Compute Median Pixel
        # Reshape to (N, 3) to compute median along axis 0
        bgr_median = np.median(roi_trimmed.reshape(-1, 3), axis=0)
        hsv_median = np.median(hsv_roi.reshape(-1, 3), axis=0)
        lab_median = np.median(lab_roi.reshape(-1, 3), axis=0)

        # Extract values
        B, G, R = bgr_median
        H, S, V = hsv_median
        L_star, a_star, b_star = lab_median

        # Hue conversion (OpenCV 0-180 -> 0-360)
        H_360 = H * 2.0

        # 5. Compute Spoilage Score
        spoilage_score = 0.0
        if name == "BCG":
            denom = (BCG_HUE_SPOILED - BCG_HUE_FRESH)
            val = (H_360 - BCG_HUE_FRESH) / denom if denom != 0 else 0
            spoilage_score = float(np.clip(val, 0, 1))
        
        elif name == "BTB":
            denom = (BTB_HUE_FRESH - BTB_HUE_SPOILED)
            val = (H_360 - BTB_HUE_SPOILED) / denom if denom != 0 else 0
            spoilage_score = float(1.0 - np.clip(val, 0, 1))
        
        elif name == "KMNO4":
            
            def circular_hue_distance(a, b):
                """Calculate shortest angular distance between two hues (0-360)."""
                d = abs(a - b)
                return min(d, 360 - d)
            
            total_range = circular_hue_distance(KMNO4_HUE_FRESH, KMNO4_HUE_SPOILED)
            current_distance = circular_hue_distance(H_360, KMNO4_HUE_FRESH)
            
            spoilage_score = float(np.clip(current_distance / total_range, 0, 1))

        results[name] = {
            "R": float(R), "G": float(G), "B": float(B),
            "H": float(H_360),
            "S": float(S), "V": float(V),
            "L_star": float(L_star), "a_star": float(a_star), "b_star": float(b_star),
            "spoilage_score": spoilage_score
        }

    return results

# --- MAIN BLOCK ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python color_extractor.py <image_path>")
        sys.exit(1)

    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        sys.exit(1)

    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Could not load image {img_path}.")
        sys.exit(1)

    results = extract_colors(img)
    
    if not results:
        print("No sticker data extracted. Check if sticker_config.json exists.")
    else:
        # Pretty print results
        print(json.dumps(results, indent=2))
        
        print("\nVisual Summary:")
        for name in ["KMNO4", "BCG", "BTB"]:
            if name in results:
                score = results[name]["spoilage_score"]
                status = get_status(score)
                print(f"  {name:5}: score={score:.2f} ({status})")

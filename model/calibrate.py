import cv2
import json
import sys
import os

# Configuration
STICKER_ORDER = ["KMNO4", "BCG", "BTB"]
COLORS = {
    "KMNO4": (255, 0, 255),  # Magenta
    "BCG": (0, 255, 0),      # Green
    "BTB": (255, 0, 0)       # Blue
}

# State
drawing = False
ix, iy = -1, -1
current_sticker_idx = 0
boxes = {}  # Store as {name: (x1, y1, x2, y2)}
temp_box = None

def mouse_callback(event, x, y, flags, param):
    global drawing, ix, iy, temp_box, current_sticker_idx, boxes

    if current_sticker_idx >= len(STICKER_ORDER):
        return

    name = STICKER_ORDER[current_sticker_idx]

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        temp_box = (ix, iy, x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp_box = (ix, iy, x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = min(ix, x), min(iy, y)
        x2, y2 = max(ix, x), max(iy, y)
        
        # Only save if the box has some area
        if x2 - x1 > 5 and y2 - y1 > 5:
            boxes[name] = (x1, y1, x2, y2)
            print(f"{name} box saved: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
            current_sticker_idx += 1
            temp_box = None
            if current_sticker_idx < len(STICKER_ORDER):
                print(f"Now draw for: {STICKER_ORDER[current_sticker_idx]}")
            else:
                print("All boxes drawn. Press 's' to save, 'r' to reset last, or 'q' to quit.")

def main():
    global current_sticker_idx, temp_box, boxes

    if len(sys.argv) < 2:
        print("Usage: python calibrate.py <image_path>")
        sys.exit(1)

    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"Error: File {img_path} not found.")
        sys.exit(1)

    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Could not decode image {img_path}.")
        sys.exit(1)

    cv2.namedWindow("Calibrate Stickers")
    cv2.setMouseCallback("Calibrate Stickers", mouse_callback)

    print(f"Calibration started. Drawing order: {', '.join(STICKER_ORDER)}")
    print(f"Now draw for: {STICKER_ORDER[current_sticker_idx]}")

    while True:
        display_img = img.copy()

        # Draw already completed boxes
        for name, box in boxes.items():
            x1, y1, x2, y2 = box
            color = COLORS[name]
            cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display_img, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Draw current temporary box
        if drawing and temp_box:
            name = STICKER_ORDER[current_sticker_idx]
            x1, y1, x2, y2 = temp_box
            color = COLORS[name]
            cv2.rectangle(display_img, (ix, iy), (x2, y2), color, 1)

        cv2.imshow("Calibrate Stickers", display_img)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("Aborted.")
            break
        elif key == ord('r'):
            if current_sticker_idx > 0:
                # If finished all, reset the last one
                if current_sticker_idx == len(STICKER_ORDER):
                    current_sticker_idx -= 1
                else:
                    # If in middle, reset the one we just finished
                    current_sticker_idx -= 1
                
                name = STICKER_ORDER[current_sticker_idx]
                if name in boxes:
                    del boxes[name]
                print(f"Reset. Now redraw for: {name}")
            else:
                print("Nothing to reset.")
        elif key == ord('s'):
            if len(boxes) == len(STICKER_ORDER):
                config = {}
                for name in STICKER_ORDER:
                    x1, y1, x2, y2 = boxes[name]
                    config[name] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                
                with open("sticker_config.json", "w") as f:
                    json.dump(config, f, indent=2)
                print("Saved to sticker_config.json")
                break
            else:
                print(f"Please draw all stickers first ({len(boxes)}/{len(STICKER_ORDER)} done).")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

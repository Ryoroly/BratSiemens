# {
#   "lh": 0,
#   "ls": 0,
#   "lv": 104,
#   "uh": 125,
#   "us": 83,
#   "uv": 255
# }

# {
#   "lh": 0,
#   "ls": 0,
#   "lv": 48,
#   "uh": 179,
#   "us": 51,
#   "uv": 241
# }

# Added shadow removal  
# {
#   "lh": 0,
#   "ls": 0,
#   "lv": 130,
#   "uh": 179,
#   "us": 51,
#   "uv": 241
# }


import cv2
import numpy as np
import os
import json
from datetime import datetime

# --- Configuration ---
IMAGE_FOLDER = "my_photos"
# IMAGE_FOLDER = "p-my_photos"
OUTPUT_DIR = "dataset_debug"
CONFIG_FILE = "threshold_config.json"
IMAGE_SIZE = (640, 640)
CLASSES = {
    "triangle": 0,
    "rectangle": 1,
    "arch": 2,
    "half-circle": 3,
    "cylinder": 4,
    "cube": 5
}

# --- Setup ---
os.makedirs(f"{OUTPUT_DIR}/images", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/labels", exist_ok=True)

# Load HSV calibration
hsv = json.load(open(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else {
    "lh": 0, "ls": 0, "lv": 0, "uh": 179, "us": 255, "uv": 255
}

def nothing(x): pass

cv2.namedWindow("Calibrate")
for k, max_val in [("lh", 179), ("ls", 255), ("lv", 255), ("uh", 179), ("us", 255), ("uv", 255)]:
    cv2.createTrackbar(k, "Calibrate", hsv[k], max_val, nothing)

def detect(frame):
    # 0. Update HSV thresholds from sliders
    for k in hsv:
        hsv[k] = cv2.getTrackbarPos(k, "Calibrate")

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 1. Only detect bright, saturated colors (ignore gray/black/white)
    lower_bound = np.array([hsv["lh"], max(hsv["ls"], 80), max(hsv["lv"], 100)])
    upper_bound = np.array([hsv["uh"], 255, 255])
    colorful_mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
    # cv2.imshow("1 - colorful_mask", colorful_mask)

    # 2. Optional: Debug HSV channels
    # cv2.imshow("Hue", hsv_frame[:, :, 0])
    # cv2.imshow("Saturation", hsv_frame[:, :, 1])
    # cv2.imshow("Value", hsv_frame[:, :, 2])

    # 3. Clean mask
    kernel = np.ones((5, 5), np.uint8)
    cleaned_mask = cv2.morphologyEx(colorful_mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    # cv2.imshow("2 - cleaned_mask", cleaned_mask)

    # 4. Show original frame with mask
    preview = cv2.bitwise_and(frame, frame, mask=cleaned_mask)
    # cv2.imshow("last (masked image)", preview)

    # 5. Invert mask for contour detection
    mask_for_detection = cv2.bitwise_not(cleaned_mask)
    mask_for_detection = cleaned_mask

    #cv2.imshow("3 - mask_for_detection", mask_for_detection)

    # 6. Contour detection and classification
    labels = []
    raw = frame.copy()
    contours, _ = cv2.findContours(mask_for_detection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) < 300:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
        v = len(approx)
        if v == 3:
            label = "triangle"
        elif v == 4:
            label = "cube" if 0.95 <= w / h <= 1.05 else "rectangle"
        elif v == 5:
            label = "arch"
        else:
            if not cv2.isContourConvex(approx):
                label = "arch"
            else:
                ratio = cv2.contourArea(cnt) / (w * h)
                label = "half-circle" if ratio < 0.7 else "cylinder"

        cv2.rectangle(raw, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(raw, label, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        H, W = frame.shape[:2]
        labels.append((CLASSES[label], (x + w / 2) / W, (y + h / 2) / H, w / W, h / H))

    return raw, labels, mask_for_detection


def save(frame, labels):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = f"{OUTPUT_DIR}/images/{ts}.jpg"
    label_path = f"{OUTPUT_DIR}/labels/{ts}.txt"

    cv2.imwrite(image_path, frame)
    with open(label_path, "w") as f:
        for cid, cx, cy, w, h in labels:
            f.write(f"{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

    print(f"Saved {ts}.jpg and {ts}.txt")

image_files = sorted([
    os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
])
if not image_files:
    print("No images found in 'my_photos'.")
    exit()

index = 0
print("Use ← and → to navigate. Press 's' to save, 'q' to quit.")

while True:
    # Load and resize image
    image_path = image_files[index]
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Could not load image: {image_path}")
        index = (index + 1) % len(image_files)
        continue

    frame = cv2.resize(frame, IMAGE_SIZE)

    # Read HSV sliders before detect
    for k in hsv:
        hsv[k] = cv2.getTrackbarPos(k, "Calibrate")

    detected_frame, labels, mask = detect(frame)

    # Combine original and detection for display
    combined = np.hstack((frame, detected_frame))
    cv2.imshow("Input | Detection", combined)

    # Show mask so user can see slider effect
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.imshow("Calibrate", mask_color)

    # waitKey with timeout so window refreshes and tracks keys
    key = cv2.waitKey(30) & 0xFF

    if key != 255:  # If any key is pressed
        print(key)

        if key == 91:  # '[' to go left
            index = (index - 1) % len(image_files)
        elif key == 93:  # ']' to go right
            index = (index + 1) % len(image_files)
        elif key == ord('s'):  # save
            save(detected_frame, labels)
        elif key == ord('q'):  # quit and save config
            with open(CONFIG_FILE, "w") as f:
                json.dump(hsv, f, indent=2)
            break


cv2.destroyAllWindows()

# {
#   "lh": 0,
#   "ls": 0,
#   "lv": 104,
#   "uh": 125,
#   "us": 83,
#   "uv": 255
# }


import cv2
import numpy as np
import os
import json
from datetime import datetime

# --- Configuration ---
IMAGE_FOLDER = "my_photos"
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
    for k in hsv:
        hsv[k] = cv2.getTrackbarPos(k, "Calibrate")

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv_frame,
        np.array([hsv["lh"], hsv["ls"], hsv["lv"]]),
        np.array([hsv["uh"], hsv["us"], hsv["uv"]])
    )
    mask = cv2.bitwise_not(mask)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    labels = []
    raw = frame.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) < 300:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
        vertices = len(approx)

        if vertices == 3:
            label = "triangle"
        elif vertices == 4:
            label = "cube" if 0.95 <= w / h <= 1.05 else "rectangle"
        elif vertices == 5:
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

    return raw, labels, mask

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
    image_path = image_files[index]
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Could not load image: {image_path}")
        index = (index + 1) % len(image_files)
        continue

    frame = cv2.resize(frame, IMAGE_SIZE)
    detected_frame, labels, mask = detect(frame)

    if frame.shape != detected_frame.shape:
        detected_frame = cv2.resize(detected_frame, (frame.shape[1], frame.shape[0]))

    combined = np.hstack((frame, detected_frame))
    cv2.imshow("Input | Detection", combined)

    # Show mask in calibration window so you can see effect of sliders
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.imshow("Calibrate", mask_color)

    key = cv2.waitKey(30) & 0xFF
    # Print key for debugging arrow keys
    if key != 255:
        print(f"Pressed key code: {key}")

    if key == ord("s"):
        save(detected_frame, labels)
    elif key == ord("q"):
        with open(CONFIG_FILE, "w") as f:
            json.dump(hsv, f, indent=2)
        break
    elif key == 81 or key == 2424832:  # Left arrow key
        index = (index - 1) % len(image_files)
    elif key == 83 or key == 2555904:  # Right arrow key
        index = (index + 1) % len(image_files)

cv2.destroyAllWindows()

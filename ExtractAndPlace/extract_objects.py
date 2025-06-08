import cv2
import numpy as np
import os
import json

# --- Configurare ---
IMAGE_FOLDER = "my_photos"
CONFIG_FILE = "threshold_config.json"
OUTPUT_FOLDER = "objects"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CLASSES = {
    "triangle": 0,
    "rectangle": 1,
    "arch": 2,
    "half-circle": 3,
    "cylinder": 4,
    "cube": 5
}

# Încarcă HSV calibrat
if os.path.exists(CONFIG_FILE):
    hsv = json.load(open(CONFIG_FILE))
else:
    hsv = {"lh": 0, "ls": 0, "lv": 0, "uh": 179, "us": 51, "uv": 241}

def classify_shape(cnt, w, h):
    approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
    v = len(approx)

    if v == 3:
        return "triangle"
    elif v == 4:
        # folosește bounding box rotit pentru a evita probleme la pătrate înclinate
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        side_lengths = [np.linalg.norm(box[i] - box[(i+1)%4]) for i in range(4)]
        side_lengths.sort()
        short, long_ = side_lengths[0], side_lengths[-1]
        aspect_ratio = short / long_
        if aspect_ratio >= 0.70:
            return "cube"
        else:
            return "rectangle"
    elif v == 5:
        return "arch"
    else:
        if not cv2.isContourConvex(approx):
            return "arch"
        else:
            ratio = cv2.contourArea(cnt) / (w * h)
            return "half-circle" if ratio < 0.7 else "cylinder"


def extract_objects(image_path, idx):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (640, 640))
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([hsv["lh"], max(hsv["ls"], 80), max(hsv["lv"], 100)])
    upper = np.array([hsv["uh"], 255, 255])
    mask = cv2.inRange(hsv_img, lower, upper)

    # Curățare mască
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for i, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < 300:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        obj = img[y:y+h, x:x+w]
        alpha = mask[y:y+h, x:x+w]

        shape = classify_shape(cnt, w, h)

        b, g, r = cv2.split(obj)
        rgba = cv2.merge((b, g, r, alpha))
        filename = f"{shape}_{idx}_{i}.png"
        out_path = os.path.join(OUTPUT_FOLDER, filename)
        cv2.imwrite(out_path, rgba)
        print(f"[Salvat] {filename}")

# --- Rulează pe toate imaginile ---
image_files = sorted([f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
for i, file in enumerate(image_files):
    extract_objects(os.path.join(IMAGE_FOLDER, file), i)

print("✅ Extragere finalizată.")

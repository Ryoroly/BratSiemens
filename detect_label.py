import cv2
import numpy as np
import os
import json
from collections import defaultdict, Counter
from datetime import datetime
import functools

# --- Configuration ---
IMAGE_FOLDER = "my_photos"
OUTPUT_DIR = "dataset_debug"
IMAGE_SIZE = (640, 640)
CLASSES = {
    "triangle": 0,
    "rectangle": 1,
    "arch": 2,
    "half-circle": 3,
    "cylinder": 4,
    "cube": 5
}

TOLERANCE = 0.03
os.makedirs(f"{OUTPUT_DIR}/images", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/labels", exist_ok=True)

# HSV Configs
HSV_CONFIGS = [
    {"lh": 0, "ls": 80, "lv": 100, "uh": 179, "us": 255, "uv": 255},
    {"lh": 0, "ls": 0, "lv": 104, "uh": 125, "us": 83, "uv": 255},
    {"lh": 0, "ls": 0, "lv": 130, "uh": 179, "us": 51, "uv": 241}
]

COLOR_RANGES = {
    "red": [(0, 100, 100), (10, 255, 255)],
    "green": [(40, 100, 100), (85, 255, 255)],
    "blue": [(100, 100, 100), (140, 255, 255)],
    "yellow": [(20, 100, 100), (35, 255, 255)]
}

def detect_hsv(frame, config):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([config["lh"], config["ls"], config["lv"]])
    upper = np.array([config["uh"], config["us"], config["uv"]])
    mask = cv2.inRange(hsv, lower, upper)
    return mask

def detect_color_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    masks = [cv2.inRange(hsv, np.array(low), np.array(high)) for low, high in COLOR_RANGES.values()]
    return functools.reduce(cv2.bitwise_or, masks)

def detect_saturation_brightness(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (0, 80, 100), (179, 255, 255))

def detect_blur_threshold(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

def detect_sharpen_edge(frame):
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharp = cv2.filter2D(frame, -1, kernel)
    gray = cv2.cvtColor(sharp, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    return mask

def find_shapes(frame, mask):
    labels = []
    kernel = np.ones((5,5), np.uint8)
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = frame.shape[:2]
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
        labels.append((label, (x + w / 2)/W, (y + h / 2)/H, w/W, h/H))
    return labels

def vote_on_detections(detections, tolerance=TOLERANCE):
    matched = []
    for det_list in detections:
        for obj in det_list:
            label, cx, cy, w, h = obj
            found = False
            for item in matched:
                dx, dy = item['center']
                if np.sqrt((cx - dx)**2 + (cy - dy)**2) < tolerance:
                    item['votes'].append(label)
                    found = True
                    break
            if not found:
                matched.append({'center': (cx, cy), 'size': (w, h), 'votes': [label]})
    results = []
    for obj in matched:
        count = Counter(obj['votes'])
        label, pct = count.most_common(1)[0]
        pct_val = int(100 * pct / sum(count.values()))
        cx, cy = obj['center']
        w, h = obj['size']
        results.append((label, pct_val, cx, cy, w, h))
    return results

def draw_results(frame, results):
    H, W = frame.shape[:2]
    for label, pct, cx, cy, w, h in results:
        x1, y1 = int((cx - w/2) * W), int((cy - h/2) * H)
        x2, y2 = int((cx + w/2) * W), int((cy + h/2) * H)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} ({pct}%)", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return frame

def save_results(image, detections, name):
    cv2.imwrite(f"{OUTPUT_DIR}/images/{name}.jpg", image)
    with open(f"{OUTPUT_DIR}/labels/{name}.txt", "w") as f:
        for label, pct, cx, cy, w, h in detections:
            f.write(f"{CLASSES[label]} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

# --- DEBUGGING WINDOW ---
def debug_filters(image_files):
    image_index = 0
    filter_index = 0

    filter_funcs = [
        lambda f: detect_hsv(f, HSV_CONFIGS[0]),
        lambda f: detect_hsv(f, HSV_CONFIGS[1]),
        lambda f: detect_hsv(f, HSV_CONFIGS[2]),
        detect_color_mask,
        detect_saturation_brightness,
        detect_blur_threshold,
        detect_sharpen_edge
    ]
    filter_labels = ["HSV1", "HSV2", "HSV3", "ColorMask", "SatBright", "BlurThresh", "SharpenEdge"]

    while True:
        frame = cv2.imread(image_files[image_index])
        if frame is None:
            print("Image not found")
            break
        frame = cv2.resize(frame, IMAGE_SIZE)

        mask = filter_funcs[filter_index](frame)
        vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        label = filter_labels[filter_index] + f" [{filter_index+1}/{len(filter_funcs)}]"
        cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.imshow("Debug Filter Viewer", vis)
        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):
            break
        elif key == 91:  # [
            filter_index = (filter_index - 1) % len(filter_funcs)
        elif key == 93:  # ]
            filter_index = (filter_index + 1) % len(filter_funcs)
        elif key == ord('a'):  # previous image
            image_index = (image_index - 1) % len(image_files)
        elif key == ord('d'):  # next image
            image_index = (image_index + 1) % len(image_files)

    cv2.destroyAllWindows()

# --- DEBUGGING WINDOW ---
image_files = sorted([
    os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
])

if image_files:
    debug_filters(image_files)

for path in image_files:
    name = os.path.splitext(os.path.basename(path))[0]
    frame = cv2.imread(path)
    if frame is None:
        continue
    frame = cv2.resize(frame, IMAGE_SIZE)
    detections = []
    for config in HSV_CONFIGS:
        mask = detect_hsv(frame, config)
        detections.append(find_shapes(frame, mask))
    detections.append(find_shapes(frame, detect_color_mask(frame)))
    detections.append(find_shapes(frame, detect_saturation_brightness(frame)))
    detections.append(find_shapes(frame, detect_blur_threshold(frame)))
    detections.append(find_shapes(frame, detect_sharpen_edge(frame)))

    final = vote_on_detections(detections)
    output = draw_results(frame.copy(), final)
    save_results(output, final, name)
    print(f"Processed: {name}")

cv2.destroyAllWindows()

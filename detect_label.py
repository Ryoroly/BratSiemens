import cv2
import numpy as np
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# === CONFIG ===
output_dir = "dataset_debug"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)
config_path = "threshold_config.json"

# === CLASE DE FORME ===
classes = {
    "triangle": 0, "rectangle": 1, "arch": 2,
    "half-circle": 3, "cylinder": 4, "cube": 5
}

calib = {
    "blur": 5,
    "threshold": 60
}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        calib.update(json.load(f))

# === FUNCȚIE DETECȚIE ===
def detect_shapes_and_label(frame, threshold_val, blur_val):
    labeled_objects = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_val = blur_val | 1  # asigură că e impar
    blurred = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)
    _, thresh = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 300:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
        vertices = len(approx)
        x, y, w, h = cv2.boundingRect(contour)

        shape_label = "unidentified"
        if vertices == 3:
            shape_label = "triangle"
        elif vertices == 4:
            aspect_ratio = w / float(h)
            shape_label = "cube" if 0.95 <= aspect_ratio <= 1.05 else "rectangle"
        elif vertices == 5:
            shape_label = "arch"
        else:
            if not cv2.isContourConvex(approx):
                shape_label = "arch"
            else:
                fill_ratio = area / float(w * h)
                shape_label = "half-circle" if fill_ratio < 0.7 else "cylinder"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, shape_label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        H, W = frame.shape[:2]
        cx, cy = x + w/2, y + h/2
        labeled_objects.append((classes[shape_label], cx/W, cy/H, w/W, h/H))

    return frame, labeled_objects

# === SALVARE ===
def save_frame_and_labels(frame, labels):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(output_dir, "images", f"{timestamp}.jpg")
    label_path = os.path.join(output_dir, "labels", f"{timestamp}.txt")
    cv2.imwrite(img_path, frame)
    with open(label_path, "w") as f:
        for cls_id, cx, cy, w, h in labels:
            f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
    print(f"[SALVAT] {img_path} + {label_path}")

# === STREAM ===
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[EROARE] Webcam-ul nu merge.")
    exit()

# === MATPLOTLIB FIGURE + SLIDERS ===
plt.ion()
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)
img_display = ax.imshow(np.zeros((480, 640, 3), dtype=np.uint8))
plt.axis("off")

# === SLIDERS ===
axthresh = plt.axes([0.15, 0.1, 0.65, 0.03])
axblur = plt.axes([0.15, 0.05, 0.65, 0.03])
sthresh = Slider(axthresh, 'Threshold', 0, 255, valinit=calib["threshold"], valstep=1)
sblur = Slider(axblur, 'Blur', 1, 49, valinit=calib["blur"] | 1, valstep=2)

frame_data = {"frame": None, "labels": []}

def update_fig():
    ret, frame = cap.read()
    if not ret:
        return
    t = int(sthresh.val)
    b = int(sblur.val)
    processed, labels = detect_shapes_and_label(frame.copy(), t, b)
    frame_data["frame"] = frame.copy()
    frame_data["labels"] = labels
    img_display.set_data(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
    fig.canvas.draw_idle()

def on_key(event):
    if event.key == 'c':
        if frame_data["frame"] is not None:
            save_frame_and_labels(frame_data["frame"], frame_data["labels"])
    elif event.key == 'q':
        print("[IESIRE] Salvez configurarea...")
        with open(config_path, "w") as f:
            json.dump({
                "threshold": int(sthresh.val),
                "blur": int(sblur.val)
            }, f, indent=2)
        plt.close()

fig.canvas.mpl_connect('key_press_event', on_key)

print("[INFO] Apasă C pentru captură și Q pentru ieșire.")
while plt.fignum_exists(fig.number):
    update_fig()
    plt.pause(0.01)

cap.release()

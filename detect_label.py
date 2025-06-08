import cv2
import numpy as np
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# === CONFIG ===
image_folder = "my_photos"
output_dir = "dataset_debug"
config_path = "threshold_config.json"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)

classes = {
    "triangle": 0, "rectangle": 1, "arch": 2,
    "half-circle": 3, "cylinder": 4, "cube": 5
}

# Load or set defaults
calib = {
    "blur": 5,
    "threshold": 60
}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        calib.update(json.load(f))

# === Load all image paths ===
image_paths = sorted([
    os.path.join(image_folder, f)
    for f in os.listdir(image_folder)
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
])
if not image_paths:
    raise FileNotFoundError("No images found in folder.")

img_index = 0
frame_data = {"frame": None, "labels": []}

# === Detection function ===
def detect_shapes_and_label(frame, threshold_val, blur_val):
    labeled_objects = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_val = blur_val | 1
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

def save_frame_and_labels(frame, labels):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(output_dir, "images", f"{timestamp}.jpg")
    label_path = os.path.join(output_dir, "labels", f"{timestamp}.txt")
    cv2.imwrite(img_path, frame)
    with open(label_path, "w") as f:
        for cls_id, cx, cy, w, h in labels:
            f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
    print(f"[SALVAT] {img_path} + {label_path}")

# === Matplotlib Figure ===
plt.ion()
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)
img_display = ax.imshow(np.zeros((640, 640, 3), dtype=np.uint8))
plt.axis("off")

# === Sliders ===
axthresh = plt.axes([0.15, 0.1, 0.65, 0.03])
axblur = plt.axes([0.15, 0.05, 0.65, 0.03])
sthresh = Slider(axthresh, 'Threshold', 0, 255, valinit=calib["threshold"], valstep=1)
sblur = Slider(axblur, 'Blur', 1, 49, valinit=calib["blur"] | 1, valstep=2)

def update_fig():
    image_path = image_paths[img_index]
    frame = cv2.imread(image_path)
    if frame is None:
        return
    frame = cv2.resize(frame, (640, 640))  # 💡 Downscale here
    t = int(sthresh.val)
    b = int(sblur.val)
    processed, labels = detect_shapes_and_label(frame.copy(), t, b)
    frame_data["frame"] = frame.copy()
    frame_data["labels"] = labels
    img_display.set_data(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
    fig.canvas.draw_idle()
    fig.suptitle(f"{os.path.basename(image_path)} [{img_index+1}/{len(image_paths)}]")

# Update on slider move
def on_slider_change(val):
    update_fig()

sthresh.on_changed(on_slider_change)
sblur.on_changed(on_slider_change)

def on_key(event):
    global img_index
    if event.key == 'left':
        img_index = (img_index - 1) % len(image_paths)
        update_fig()
    elif event.key == 'right':
        img_index = (img_index + 1) % len(image_paths)
        update_fig()
    elif event.key == 's':
        if frame_data["frame"] is not None:
            save_frame_and_labels(frame_data["frame"], frame_data["labels"])
    elif event.key == 'q':
        with open(config_path, "w") as f:
            json.dump({
                "threshold": int(sthresh.val),
                "blur": int(sblur.val)
            }, f, indent=2)
        print("[IESIRE] Configurație salvată.")
        plt.close()

fig.canvas.mpl_connect('key_press_event', on_key)

print("Folosește ← și → pentru imagini, S pentru salvare, Q pentru ieșire.")
update_fig()
while plt.fignum_exists(fig.number):
    plt.pause(0.01)

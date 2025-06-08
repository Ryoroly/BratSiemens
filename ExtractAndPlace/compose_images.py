import cv2
import numpy as np
import os
import random

OBJECT_FOLDER = "objects"
BACKGROUND_FOLDER = "backgrounds"
OUTPUT_IMAGES = "dataset/images"
OUTPUT_LABELS = "dataset/labels"
os.makedirs(OUTPUT_IMAGES, exist_ok=True)
os.makedirs(OUTPUT_LABELS, exist_ok=True)

CLASSES = {
    "triangle": 0,
    "rectangle": 1,
    "arch": 2,
    "half-circle": 3,
    "cylinder": 4,
    "cube": 5
}

def overlay_image(bg, fg, x, y):
    h, w = fg.shape[:2]
    if y + h > bg.shape[0] or x + w > bg.shape[1]:
        return bg  # skip dacă depășește fundalul

    alpha = fg[:, :, 3] / 255.0
    for c in range(3):
        bg[y:y+h, x:x+w, c] = alpha * fg[:, :, c] + (1 - alpha) * bg[y:y+h, x:x+w, c]
    return bg

def generate_synthetic_images():
    bg_files = [f for f in os.listdir(BACKGROUND_FOLDER) if f.endswith(('.jpg', '.png'))]
    obj_files = [f for f in os.listdir(OBJECT_FOLDER) if f.endswith('.png')]

    for i in range(100):  # Generează 100 imagini sintetice
        bg_path = os.path.join(BACKGROUND_FOLDER, random.choice(bg_files))
        bg = cv2.imread(bg_path)
        bg = cv2.resize(bg, (640, 640))

        n_objects = random.randint(1, 3)
        selected_objs = random.sample(obj_files, n_objects)
        label_lines = []

        for obj_name in selected_objs:
            fg = cv2.imread(os.path.join(OBJECT_FOLDER, obj_name), cv2.IMREAD_UNCHANGED)
            cls_name = obj_name.split("_")[0]  # Ex: triangle_1.png
            cls_id = CLASSES.get(cls_name, 0)
            h, w = fg.shape[:2]
            x = random.randint(0, 640 - w)
            y = random.randint(0, 640 - h)
            bg = overlay_image(bg, fg, x, y)

            cx = (x + w/2) / 640
            cy = (y + h/2) / 640
            nw = w / 640
            nh = h / 640
            label_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        img_path = f"{OUTPUT_IMAGES}/synth_{i}.jpg"
        label_path = f"{OUTPUT_LABELS}/synth_{i}.txt"
        cv2.imwrite(img_path, bg)
        with open(label_path, "w") as f:
            f.write("\n".join(label_lines))
        print(f"Creat: {img_path}")

generate_synthetic_images()

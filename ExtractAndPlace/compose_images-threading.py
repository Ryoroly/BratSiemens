import cv2
import numpy as np
import os
import random
import multiprocessing as mp
from functools import partial
from compose_images import add_shadow_smooth_pro, overlay_image


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

def make_image(idx, bg_files, obj_files, shadow_prob):
    bg = cv2.imread(random.choice(bg_files))
    bg = cv2.resize(bg, (640, 640))
    labels = []

    for _ in range(random.randint(1, 3)):
        fg_name = random.choice(obj_files)
        fg_path = os.path.join(OBJECT_FOLDER, fg_name)
        fg = cv2.imread(fg_path, cv2.IMREAD_UNCHANGED)
        if fg is None or fg.shape[2] != 4:
            continue

        cls = fg_name.split("_")[0]
        cls_id = CLASSES.get(cls, 0)
        h, w = fg.shape[:2]
        x = random.randint(0, 640 - w)
        y = random.randint(0, 640 - h)

        if random.random() < shadow_prob:
            bg = add_shadow_smooth_pro(
                fg, bg, x, y,
                direction=(15, 15),
                blur_gauss=121,
                use_bilateral=True,
                bilateral_params=(15, 100, 100),
                opacity=0.35
            )
        else:
            bg = overlay_image(bg, fg, x, y)

        cx, cy = (x + w / 2) / 640, (y + h / 2) / 640
        nw, nh = w / 640, h / 640
        labels.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

    img_path = os.path.join(OUTPUT_IMAGES, f"synth_{idx:04d}.jpg")
    lbl_path = os.path.join(OUTPUT_LABELS, f"synth_{idx:04d}.txt")
    cv2.imwrite(img_path, bg)
    with open(lbl_path, 'w') as f:
        f.write('\n'.join(labels))
    return idx

def generate_all(num_images=100, shadow_prob=0.7):
    bg_files = [
        os.path.join(BACKGROUND_FOLDER, f)
        for f in os.listdir(BACKGROUND_FOLDER)
        if f.lower().endswith(('.jpg', '.png'))
    ]
    obj_files = [
        f for f in os.listdir(OBJECT_FOLDER)
        if f.lower().endswith('.png')
    ]
    func = partial(make_image, bg_files=bg_files, obj_files=obj_files, shadow_prob=shadow_prob)

    with mp.Pool(mp.cpu_count()) as pool:
        for idx in pool.imap_unordered(func, range(num_images)):
            print(f"[DONE] synth_{idx:04d}.jpg")

if __name__ == '__main__':
    generate_all(num_images=200, shadow_prob=0.7)

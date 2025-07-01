# lab/visualizer.py

import os, random
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

DATASET_DIR = "dataset"
SPLIT = "train"
NUM_IMAGES = 5
CLASSES = ["triangle", "half circle", "cube", "rectangle", "cylinder", "arch"]

label_dir = os.path.join(DATASET_DIR, "labels", SPLIT)
label_files = random.sample(os.listdir(label_dir), NUM_IMAGES)

for label_file in label_files:
    image_file = label_file.replace(".txt", ".jpeg")
    img_path = os.path.join(DATASET_DIR, "images", SPLIT, image_file)
    label_path = os.path.join(label_dir, label_file)

    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    with open(label_path) as f:
        for line in f:
            parts = line.strip().split()
            cls_id = int(parts[0])
            xc, yc, bw, bh = map(float, parts[1:])
            x1 = (xc - bw / 2) * w
            y1 = (yc - bh / 2) * h
            x2 = (xc + bw / 2) * w
            y2 = (yc + bh / 2) * h
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            draw.text((x1, y1 - 10), CLASSES[cls_id], fill="red")

    plt.figure(figsize=(6, 6))
    plt.imshow(img)
    plt.title(image_file)
    plt.axis("off")
    plt.show()

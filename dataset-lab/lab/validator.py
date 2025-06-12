# lab/validator.py

import os
import pandas as pd
from collections import Counter

DATASET_DIR = "dataset"
CLASSES = ["triangle", "half circle", "cube", "rectangle", "cylinder", "arch"]

def collect_stats(split):
    labels_dir = os.path.join(DATASET_DIR, "labels", split)
    class_counts = Counter()

    for label_file in os.listdir(labels_dir):
        with open(os.path.join(labels_dir, label_file)) as f:
            for line in f:
                cls_id = int(line.strip().split()[0])
                class_counts[cls_id] += 1

    df = pd.DataFrame({
        'class_id': class_counts.keys(),
        'class_name': [CLASSES[i] for i in class_counts.keys()],
        'count': class_counts.values()
    })

    print(f"\nStats for {split}:")
    print(df)

for split in ["train", "val", "test"]:
    collect_stats(split)

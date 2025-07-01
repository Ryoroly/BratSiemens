# lab/cleaner.py

import os

DATASET_DIR = "dataset"
SPLIT = "train"

labels_dir = os.path.join(DATASET_DIR, "labels", SPLIT)
empty_files = []

for label_file in os.listdir(labels_dir):
    label_path = os.path.join(labels_dir, label_file)
    with open(label_path) as f:
        lines = f.readlines()
        if len(lines) == 0:
            empty_files.append(label_file)

print("\n⚠ Empty label files:")
for f in empty_files:
    print(f)

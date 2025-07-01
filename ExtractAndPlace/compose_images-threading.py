import os
import random
import shutil
import yaml
import cv2
import time
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
from compose_images import add_shadow_smooth_pro, overlay_image

NUM_THREADS = 4
CLASSES = {
    "triangle": 0,
    "rectangle": 1,
    "arch": 2,
    "half-circle": 3,
    "cylinder": 4,
    "cube": 5
}
CLASS_NAMES = list(CLASSES.keys())

def safe_imwrite(path, img, retries=3, delay=0.2):
    for i in range(retries):
        if cv2.imwrite(path, img):
            return True
        time.sleep(delay)
    print(f"[ERROR] Could not write image: {path}")
    return False

def make_synth(idx, bg_files, obj_files, shadow_prob, object_folder, out_img, out_lbl):
    bg = cv2.resize(cv2.imread(random.choice(bg_files)), (640, 640))
    labels = []

    for _ in range(random.randint(1, 3)):
        fg_name = random.choice(obj_files)
        fg = cv2.imread(os.path.join(object_folder, fg_name), cv2.IMREAD_UNCHANGED)
        if fg is None or fg.shape[2] != 4:
            continue

        cls_name = fg_name.split("_")[0]
        cls_id = CLASSES[cls_name]
        h, w = fg.shape[:2]
        x = random.randint(0, 640 - w)
        y = random.randint(0, 640 - h)

        if random.random() < shadow_prob:
            bg = add_shadow_smooth_pro(fg, bg, x, y,
                                       direction=(15, 15), blur_gauss=121,
                                       use_bilateral=True,
                                       bilateral_params=(15, 100, 100),
                                       opacity=0.35)
        else:
            bg = overlay_image(bg, fg, x, y)

        cx, cy = (x + w / 2) / 640, (y + h / 2) / 640
        nw, nh = w / 640, h / 640
        labels.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

    img_path = os.path.join(out_img, f"synth_{idx:04d}.jpg")
    lbl_path = os.path.join(out_lbl, f"synth_{idx:04d}.txt")
    safe_imwrite(img_path, bg)
    with open(lbl_path, 'w') as f:
        f.write("\n".join(labels))

def create_dataset(output_folder="dataset", n=200, split_ratio=0.8):
    tmp_img = os.path.join(output_folder, r"all\images")
    tmp_lbl = os.path.join(output_folder, r"all\labels")
    for d in [tmp_img, tmp_lbl]:
        os.makedirs(d, exist_ok=True)

    bg_files = [os.path.join("backgrounds", f) for f in os.listdir("backgrounds") if f.lower().endswith(('.jpg', '.png'))]
    obj_files = [f for f in os.listdir("objects") if f.lower().endswith('.png')]

    func = partial(make_synth,
                   bg_files=bg_files,
                   obj_files=obj_files,
                   shadow_prob=0.7,
                   object_folder="objects",
                   out_img=tmp_img,
                   out_lbl=tmp_lbl)

    with mp.Pool(NUM_THREADS) as pool:
        for _ in tqdm(pool.imap(func, range(n)), total=n):
            pass

    items = sorted(os.listdir(tmp_img))
    random.shuffle(items)
    split = int(len(items) * split_ratio)
    for i, fname in enumerate(items):
        subset = "train" if i < split else "val"
        for sub in ["images", "labels"]:
            os.makedirs(os.path.join(output_folder, subset, sub), exist_ok=True)
        shutil.move(os.path.join(tmp_img, fname), os.path.join(output_folder, subset, "images", fname))
        lname = fname.replace(".jpg", ".txt")
        shutil.move(os.path.join(tmp_lbl, lname), os.path.join(output_folder, subset, "labels", lname))

def write_data_yaml(output_folder="dataset"):
    data = {
        "train": os.path.join("train/images"),
        "val":   os.path.join("val/images"),
        "nc":    len(CLASS_NAMES),
        "names": CLASS_NAMES
    }
    with open(os.path.join(output_folder, "data.yaml"), "w") as f:
        yaml.safe_dump(data, f)

if __name__ == "__main__":
    create_dataset(n=1000, split_ratio=0.8)
    write_data_yaml()
    print("✅ Dataset ready with YOLO‑compatible structure and data.yaml")

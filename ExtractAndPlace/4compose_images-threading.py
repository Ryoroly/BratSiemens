import os
import random
import shutil
import yaml
import cv2
import time
import numpy as np
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
from compose_images import add_shadow_smooth_pro, overlay_image

NUM_THREADS = 8
CLASSES = {
    "triangle": 0,
    "rectangle": 1,
    "arch": 2,
    "cube": 3
}
CLASS_NAMES = list(CLASSES.keys())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bck_path = os.path.join(BASE_DIR, "backgrounds")
objects_path = os.path.join(BASE_DIR, "polished_objects")


def safe_imwrite(path, img, retries=3, delay=0.2):
    for _ in range(retries):
        if cv2.imwrite(path, img):
            return True
        time.sleep(delay)
    print(f"[ERROR] Could not write image: {path}")
    return False


def boxes_overlap(box1, box2):
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    return not (x1_max <= x2_min or x1_min >= x2_max or y1_max <= y2_min or y1_min >= y2_max)


def rotate_image(img, angle):
    h0, w0 = img.shape[:2]
    center = (w0 / 2, h0 / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # compute new bounds
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    new_w = int((h0 * sin) + (w0 * cos))
    new_h = int((h0 * cos) + (w0 * sin))
    # adjust translation
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    # rotate with transparent background
    return cv2.warpAffine(
        img, M, (new_w, new_h), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )


def make_synth(idx, bg_files, obj_files_by_class, shadow_prob,
               object_folder, out_img, out_lbl,
               min_objs=2, max_objs=4, max_angle=45):
    bg = cv2.resize(cv2.imread(random.choice(bg_files)), (640, 550))
    labels = []
    placed_boxes = []

    available_classes = [cls for cls in CLASSES if obj_files_by_class[cls]]
    if not available_classes:
        print(f"[ERROR] No objects available for any class, skipping idx {idx}")
        return

    num_objs = random.randint(min_objs, max_objs)
    classes_for_image = random.choices(available_classes, k=num_objs)

    for cls_name in classes_for_image:
        fg_list = obj_files_by_class[cls_name]
        if not fg_list:
            print(f"[WARN] No objects for class {cls_name}, skipping object")
            continue
        fg_name = random.choice(fg_list)
        fg_path = os.path.join(object_folder, fg_name)
        fg = cv2.imread(fg_path, cv2.IMREAD_UNCHANGED)
        if fg is None or fg.shape[2] != 4:
            print(f"[WARN] Invalid object (missing alpha): {fg_name}")
            continue

        # Apply random rotation
        angle = random.uniform(-max_angle, max_angle)
        fg_rot = rotate_image(fg, angle)
        h, w = fg_rot.shape[:2]

        # find non-zero alpha mask box in rotated image
        mask = fg_rot[:, :, 3] > 0
        ys, xs = np.where(mask)
        if ys.size == 0 or xs.size == 0:
            continue
        y0, y1 = ys.min(), ys.max()
        x0, x1 = xs.min(), xs.max()
        obj_h = y1 - y0 + 1
        obj_w = x1 - x0 + 1

        placed = False
        for _ in range(50):
            x = random.randint(0, 640 - w)
            y = random.randint(0, 550 - h)
            # compute bbox for mask region
            box = (x + x0, y + y0, x + x1, y + y1)
            if all(not boxes_overlap(box, b) for b in placed_boxes):
                placed_boxes.append(box)
                placed = True
                break

        if not placed:
            print(f"[WARN] Could not place {cls_name} without overlap in idx {idx}")
            continue

        # overlay shadow
        if random.random() < shadow_prob:
            bg = add_shadow_smooth_pro(fg_rot, bg, x, y,
                                       direction=(15, 15), blur_gauss=121,
                                       use_bilateral=True,
                                       bilateral_params=(15, 100, 100),
                                       opacity=0.35)
        # overlay rotated object
        bg = overlay_image(bg, fg_rot, x, y)

        # compute normalized YOLO bbox from mask
        bx_min, by_min, bx_max, by_max = box
        cx = ((bx_min + bx_max) / 2) / 640
        cy = ((by_min + by_max) / 2) / 550
        nw = (bx_max - bx_min) / 640
        nh = (by_max - by_min) / 550
        labels.append(f"{CLASSES[cls_name]} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

    if labels:
        img_path = os.path.join(out_img, f"synth_{idx:04d}.jpg")
        lbl_path = os.path.join(out_lbl, f"synth_{idx:04d}.txt")
        safe_imwrite(img_path, bg)
        with open(lbl_path, 'w') as f:
            f.write("\n".join(labels))


def make_synth_job(idx, *args, **kwargs):
    make_synth(idx=idx, *args, **kwargs)

def create_dataset(output_folder="dataset", n_per_class=250, split_ratio=0.8):
    tmp_img = os.path.join(output_folder, "all", "images")
    tmp_lbl = os.path.join(output_folder, "all", "labels")
    os.makedirs(tmp_img, exist_ok=True)
    os.makedirs(tmp_lbl, exist_ok=True)

    bg_files = [os.path.join(bck_path, f) for f in os.listdir(bck_path) if f.lower().endswith(('.jpg', '.png'))]
    obj_files = [f for f in os.listdir(objects_path) if f.lower().endswith('.png')]

    obj_files_by_class = {cls: [] for cls in CLASSES}
    for f in obj_files:
        for cls in CLASSES:
            if cls in f.lower():
                obj_files_by_class[cls].append(f)

    num_images = n_per_class * len(CLASSES)
    jobs = list(range(num_images))
    random.shuffle(jobs)

    func = partial(
        make_synth_job,
        bg_files=bg_files,
        obj_files_by_class=obj_files_by_class,
        shadow_prob=0.7,
        object_folder=objects_path,
        out_img=tmp_img,
        out_lbl=tmp_lbl
    )

    with mp.Pool(NUM_THREADS) as pool:
        list(tqdm(pool.map(func, jobs), total=len(jobs)))

    all_imgs = [f for f in os.listdir(tmp_img) if f.endswith(".jpg")]
    random.shuffle(all_imgs)
    split = int(len(all_imgs) * split_ratio)
    train_imgs = all_imgs[:split]
    val_imgs = all_imgs[split:]

    for subset, files in [("train", train_imgs), ("val", val_imgs)]:
        for sub in ["images", "labels"]:
            os.makedirs(os.path.join(output_folder, subset, sub), exist_ok=True)
        for f in files:
            shutil.move(os.path.join(tmp_img, f), os.path.join(output_folder, subset, "images", f))
            lbl = f.replace(".jpg", ".txt")
            shutil.move(os.path.join(tmp_lbl, lbl), os.path.join(output_folder, subset, "labels", lbl))

    # Cleanup temp folders
    shutil.rmtree(os.path.join(output_folder, "all"))
    print(f"✅ Dataset created: {len(train_imgs)} train, {len(val_imgs)} val")

def write_data_yaml(output_folder="dataset"):
    data = {
        "train": "train/images",
        "val": "val/images",
        "nc": len(CLASS_NAMES),
        "names": CLASS_NAMES
    }
    with open(os.path.join(output_folder, "data.yaml"), "w") as f:
        yaml.safe_dump(data, f)

if __name__ == "__main__":
    create_dataset(n_per_class=500, split_ratio=0.8)
    write_data_yaml()
    print("✅ YOLO dataset ready — no overlaps, no leftover files, clean shadows.")

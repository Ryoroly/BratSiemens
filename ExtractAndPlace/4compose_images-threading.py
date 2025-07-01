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
    "cube": 3
}
CLASS_NAMES = list(CLASSES.keys())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bck_path = os.path.join(BASE_DIR, "backgrounds")
objects_path = os.path.join(BASE_DIR, "polished_objects")

def safe_imwrite(path, img, retries=3, delay=0.2):
    for i in range(retries):
        if cv2.imwrite(path, img):
            return True
        time.sleep(delay)
    print(f"[ERROR] Could not write image: {path}")
    return False

def boxes_overlap(box1, box2):
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    return not (x1_max <= x2_min or x1_min >= x2_max or y1_max <= y2_min or y1_min >= y2_max)

def make_synth(idx, bg_files, obj_files_by_class, shadow_prob, object_folder, out_img, out_lbl, min_objs=2, max_objs=4):
    bg = cv2.resize(cv2.imread(random.choice(bg_files)), (1200, 550))
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
            print(f"[WARN] No objects available for class {cls_name}, skipping object")
            continue
        fg_name = random.choice(fg_list)
        fg = cv2.imread(os.path.join(object_folder, fg_name), cv2.IMREAD_UNCHANGED)
        if fg is None or fg.shape[2] != 4:
            print(f"[WARN] Skipped invalid object: {fg_name}")
            continue

        cls_id = CLASSES[cls_name]
        h, w = fg.shape[:2]

        for attempt in range(50):
            x = random.randint(0, 1200 - w)
            y = random.randint(0, 550 - h)
            box = (x, y, x + w, y + h)

            if all(not boxes_overlap(box, b) for b in placed_boxes):
                placed_boxes.append(box)
                break
        else:
            print(f"[WARN] Could not place {cls_name} without overlap in idx {idx}")
            continue

        if random.random() < shadow_prob:
            bg = add_shadow_smooth_pro(fg, bg, x, y,
                                       direction=(15, 15), blur_gauss=121,
                                       use_bilateral=True,
                                       bilateral_params=(15, 100, 100),
                                       opacity=0.35)
        else:
            bg = overlay_image(bg, fg, x, y)

        cx, cy = (x + w / 2) / 1200, (y + h / 2) / 550
        nw, nh = w / 1200, h / 550
        labels.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

    if labels:
        img_path = os.path.join(out_img, f"synth_{idx:04d}.jpg")
        lbl_path = os.path.join(out_lbl, f"synth_{idx:04d}.txt")
        safe_imwrite(img_path, bg)
        with open(lbl_path, 'w') as f:
            f.write("\n".join(labels))


def make_synth_job(idx, bg_files, obj_files_by_class, shadow_prob, object_folder, out_img, out_lbl):
    make_synth(
        idx=idx,
        bg_files=bg_files,
        obj_files_by_class=obj_files_by_class,
        shadow_prob=shadow_prob,
        object_folder=object_folder,
        out_img=out_img,
        out_lbl=out_lbl,
        min_objs=2,
        max_objs=4
    )

def create_dataset(output_folder="dataset", n_per_class=250, split_ratio=0.8):
    tmp_img = os.path.join(output_folder, "all", "images")
    tmp_lbl = os.path.join(output_folder, "all", "labels")
    for d in [tmp_img, tmp_lbl]:
        os.makedirs(d, exist_ok=True)

    bg_files = [os.path.join(bck_path, f) for f in os.listdir(bck_path) if f.lower().endswith(('.jpg', '.png'))]
    obj_files = [f for f in os.listdir(objects_path) if f.lower().endswith('.png')]

    obj_files_by_class = {cls: [] for cls in CLASSES}
    for f in obj_files:
        for cls in CLASSES:
            if f.lower().find(cls) != -1:
                obj_files_by_class[cls].append(f)

    # generare jobs: doar număr imagini
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

    # split train/val
    all_imgs = [f for f in os.listdir(tmp_img) if f.endswith(".jpg")]
    random.shuffle(all_imgs)
    split = int(len(all_imgs) * split_ratio)
    train_imgs = all_imgs[:split]
    val_imgs = all_imgs[split:]
    for subset, files in [("train", train_imgs), ("val", val_imgs)]:
        for f in files:
            for sub in ["images", "labels"]:
                os.makedirs(os.path.join(output_folder, subset, sub), exist_ok=True)
            shutil.move(os.path.join(tmp_img, f), os.path.join(output_folder, subset, "images", f))
            lname = f.replace(".jpg", ".txt")
            shutil.move(os.path.join(tmp_lbl, lname), os.path.join(output_folder, subset, "labels", lname))

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
    create_dataset(n_per_class=250, split_ratio=0.8)
    write_data_yaml()
    print("✅ Dataset YOLO-ready, multi-class per image, no overlaps.")

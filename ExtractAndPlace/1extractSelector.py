import cv2
import numpy as np
import os
import json

# --- CONFIG ---
OUTPUT_FOLDER = "objects"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
CONFIG_FILE = "threshold_config.json"

# Initial HSV config (will load from file if exists)
hsv_config = {
    "lh": 0, "ls": 0, "lv": 0,
    "uh": 179, "us": 255, "uv": 255
}
if os.path.exists(CONFIG_FILE):
    hsv_config = json.load(open(CONFIG_FILE))

COLOR_RANGES = {
    "red": [((0, 100, 100), (10, 255, 255)), ((160, 100, 100), (179, 255, 255))],
    "green": [((40, 50, 50), (85, 255, 255))],
    "yellow": [((20, 100, 100), (35, 255, 255))],
    "pink": [((145, 100, 100), (165, 255, 255))],
    "light_blue": [((85, 100, 100), (105, 255, 255))],
    "orange": [((10, 100, 100), (20, 255, 255))],
    "blue": [((105, 100, 100), (130, 255, 255))]
}

def generate_masks(img):
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    masks = {}
    for color, ranges in COLOR_RANGES.items():
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        for (low, high) in ranges:
            mask |= cv2.inRange(hsv_img, np.array(low), np.array(high))
        masks[color] = mask
    return masks

def auto_select_top_colors(masks):
    coverage = {name: cv2.countNonZero(mask) for name, mask in masks.items()}
    sorted_colors = sorted(coverage, key=coverage.get, reverse=True)
    top_colors = [c for c in sorted_colors if coverage[c] > 0][:2]
    print(f"[Auto-selected] {top_colors}")
    return top_colors if top_colors else ["HSV_Calibrate"]

def apply_morph(mask):
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

def classify_and_save(img, mask, color_name, idx):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < 300:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        obj = img[y:y+h, x:x+w]
        alpha = mask[y:y+h, x:x+w]
        b, g, r = cv2.split(obj)
        rgba = cv2.merge((b, g, r, alpha))
        out_name = f"{color_name}_{idx}_{i}.png"
        cv2.imwrite(os.path.join(OUTPUT_FOLDER, out_name), rgba)
        print(f"[Saved] {out_name}")

def hsv_calibrate(img):
    cv2.namedWindow("HSV Calibrate")
    for k, max_val in [("lh", 179), ("ls", 255), ("lv", 255), ("uh", 179), ("us", 255), ("uv", 255)]:
        cv2.createTrackbar(k, "HSV Calibrate", hsv_config[k], max_val, lambda x: None)
    
    while True:
        for k in hsv_config:
            hsv_config[k] = cv2.getTrackbarPos(k, "HSV Calibrate")
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array([hsv_config["lh"], hsv_config["ls"], hsv_config["lv"]])
        upper = np.array([hsv_config["uh"], hsv_config["us"], hsv_config["uv"]])
        mask = cv2.inRange(hsv_img, lower, upper)
        mask = apply_morph(mask)
        mask_vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = cv2.hconcat([img, mask_vis])
        combined = resize_to_fit(combined, 1200)
        cv2.imshow("HSV Calibrate", combined)
        key = cv2.waitKey(30) & 0xFF
        if key == ord('s'):
            classify_and_save(img, mask, "HSV_Calibrate", 0)
            break
        elif key == ord('q'):
            json.dump(hsv_config, open(CONFIG_FILE, "w"), indent=2)
            break
    cv2.destroyWindow("HSV Calibrate")

def resize_to_fit(img, max_width):
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        return cv2.resize(img, (int(w * scale), int(h * scale)))
    return img

def interactive_selection(image_paths):
    for idx, path in enumerate(image_paths):
        img = cv2.imread(path)
        if img is None:
            print(f"⚠️ Could not load {path}")
            continue
        masks = generate_masks(img)
        top_colors = auto_select_top_colors(masks)
        all_options = top_colors + [c for c in masks if c not in top_colors] + ["HSV_Calibrate"]
        selected_idx = 0

        while True:
            sel = all_options[selected_idx]
            if sel == "HSV_Calibrate":
                hsv_calibrate(img)
                break
            else:
                mask = apply_morph(masks[sel])
                mask_vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                combined = cv2.hconcat([img, mask_vis])
                combined = resize_to_fit(combined, 1200)
                menu = np.ones((40, combined.shape[1], 3), dtype=np.uint8) * 50
                x = 10
                for name in all_options:
                    color = (0,255,0) if name == sel else (200,200,200)
                    cv2.putText(menu, name, (x,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color,2)
                    x += 130
                view = cv2.vconcat([combined, menu])
                cv2.imshow("Mask Selector", view)

                def click_cb(event, x_click, y_click, flags, param):
                    if event == cv2.EVENT_LBUTTONDOWN and y_click >= combined.shape[0]:
                        idx_click = x_click // 130
                        nonlocal selected_idx
                        if idx_click < len(all_options):
                            selected_idx = idx_click
                            print(f"[Manual selection] {all_options[selected_idx]}")
                cv2.setMouseCallback("Mask Selector", click_cb)

                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    return
                elif key == ord('s'):
                    classify_and_save(img, mask, sel, idx)
                    break
    cv2.destroyAllWindows()

def get_images_from_folder(folder):
    valid_ext = ('.jpg', '.jpeg', '.png', '.bmp')
    return [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if f.lower().endswith(valid_ext)
    ]

# --- SET YOUR FOLDER HERE ---
INPUT_FOLDER = "ExtractAndPlace/rawObj/objPiCamera"  # Replace with your folder
image_paths = get_images_from_folder(INPUT_FOLDER)

if not image_paths:
    print(f"⚠️ No valid images found in {INPUT_FOLDER}")
else:
    interactive_selection(image_paths)

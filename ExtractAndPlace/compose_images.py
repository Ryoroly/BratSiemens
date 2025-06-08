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

# Suprapune foreground (RGBA) peste fundal
def overlay_image(bg, fg, x, y):
    h, w = fg.shape[:2]
    if y + h > bg.shape[0] or x + w > bg.shape[1]:
        return bg
    alpha = fg[:, :, 3] / 255.0
    for c in range(3):
        bg[y:y+h, x:x+w, c] = alpha * fg[:, :, c] + (1 - alpha) * bg[y:y+h, x:x+w, c]
    return bg

# Adaugă umbră soft cu offset și blur
def add_shadow(fg_rgba, bg_bgr, x, y, direction=(20,20), blur=60, opacity=0.4):
    alpha = fg_rgba[:, :, 3]
    shadow = cv2.blur(alpha, (blur, blur))
    h_fg, w_fg = alpha.shape
    ox, oy = direction
    sx, sy = x + ox, y + oy
    
    # Restrângere regiune validă
    sy0, sy1 = max(0, sy), min(bg_bgr.shape[0], sy + h_fg)
    sx0, sx1 = max(0, sx), min(bg_bgr.shape[1], sx + w_fg)
    mh0, mw0 = sy0 - sy, sx0 - sx
    mh1, mw1 = mh0 + (sy1 - sy0), mw0 + (sx1 - sx0)
    
    shadow_region = shadow[mh0:mh1, mw0:mw1]
    alpha_norm = (shadow_region / 255.0 * opacity)
    
    for c in range(3):
        bg_bgr[sy0:sy1, sx0:sx1, c] = (
            bg_bgr[sy0:sy1, sx0:sx1, c] * (1 - alpha_norm) +
            0 * alpha_norm
        ).astype(np.uint8)
    
    return overlay_image(bg_bgr, fg_rgba, x, y)
def add_shadow_smooth_pro(
    fg_rgba, bg_bgr, x, y,
    direction=(20, 20),
    blur_gauss=101,
    use_bilateral=True, bilateral_params=(15, 75, 75),
    opacity=0.3
):
    alpha = fg_rgba[:, :, 3]
    shadow = alpha.astype(np.uint8)

    # 🌫 Aplică bilateral filter pentru a păstra conturul
    if use_bilateral:
        shadow = cv2.bilateralFilter(shadow, *bilateral_params)

    # 🌀 Aplică GaussianBlur pentru umbră difuză
    shadow = cv2.GaussianBlur(shadow, (blur_gauss, blur_gauss), 0)

    # Compunerea umbrei pe fundal
    h_fg, w_fg = shadow.shape
    ox, oy = direction
    sx, sy = x + ox, y + oy
    sy0, sy1 = max(0, sy), min(bg_bgr.shape[0], sy + h_fg)
    sx0, sx1 = max(0, sx), min(bg_bgr.shape[1], sx + w_fg)
    mh0, mw0 = sy0 - sy, sx0 - sx
    mh1 = mh0 + (sy1 - sy0)
    mw1 = mw0 + (sx1 - sx0)
    region = shadow[mh0:mh1, mw0:mw1] / 255.0 * opacity

    for c in range(3):
        bg_bgr[sy0:sy1, sx0:sx1, c] = (
            bg_bgr[sy0:sy1, sx0:sx1, c] * (1 - region)
        ).astype(np.uint8)

    return overlay_image(bg_bgr, fg_rgba, x, y)


def generate_synthetic_images(num_images=100, shadow_prob=0.7):
    bg_files = [os.path.join(BACKGROUND_FOLDER, f)
                for f in os.listdir(BACKGROUND_FOLDER)
                if f.lower().endswith(('.jpg', '.png'))]
    obj_files = [f for f in os.listdir(OBJECT_FOLDER) if f.lower().endswith('.png')]

    for i in range(num_images):
        bg = cv2.imread(random.choice(bg_files))
        bg = cv2.resize(bg, (640, 640))
        label_lines = []
        
        for _ in range(random.randint(1, 3)):
            fg_name = random.choice(obj_files)
            fg = cv2.imread(os.path.join(OBJECT_FOLDER, fg_name), cv2.IMREAD_UNCHANGED)
            cls = fg_name.split("_")[0]
            cls_id = CLASSES.get(cls, 0)
            h, w = fg.shape[:2]
            x, y = random.randint(0, 640 - w), random.randint(0, 640 - h)
            
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
            
            cx, cy = (x + w/2) / 640, (y + h/2) / 640
            nw, nh = w / 640, h / 640
            label_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
        
        img_path = os.path.join(OUTPUT_IMAGES, f"synth_{i:04d}.jpg")
        lbl_path = os.path.join(OUTPUT_LABELS, f"synth_{i:04d}.txt")
        cv2.imwrite(img_path, bg)
        with open(lbl_path, "w") as f:
            f.write("\n".join(label_lines))
        print(f"[GEN] {img_path}")

# Rulează generarea
generate_synthetic_images(num_images=50, shadow_prob=0.7)

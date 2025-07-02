import cv2
import numpy as np
import os

INPUT_FOLDER = "objects2"  # Replace with your folder containing PNGs
OUTPUT_FOLDER = "polished_objects2"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def repair_arch(path, idx):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] < 4:
        print(f"⚠️ Skipping {path}")
        return
    
    alpha = img[:, :, 3]
    kernel = np.ones((5, 5), np.uint8)
    cleaned = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
    
    # Detect largest contour
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"⚠️ No contours in {path}")
        return
    
    cnt = max(contours, key=cv2.contourArea)
    mask_clean = np.zeros_like(alpha)
    cv2.drawContours(mask_clean, [cnt], -1, 255, cv2.FILLED)
    
    b, g, r = cv2.split(img[:, :, :3])
    polished = cv2.merge((b, g, r, mask_clean))
    
    out_path = os.path.join(OUTPUT_FOLDER, f"refaced_arch_{idx}.png")
    cv2.imwrite(out_path, polished)
    print(f"[Saved] {out_path}")

def clean_and_classify(path, idx):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] < 4:
        print(f"⚠️ Skipping {path} (no alpha channel)")
        return

    alpha = img[:, :, 3]

    kernel = np.ones((5,5), np.uint8)
    cleaned = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.dilate(cleaned, kernel, iterations=1)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_filled = np.zeros_like(cleaned)
    cv2.drawContours(mask_filled, contours, -1, 255, cv2.FILLED)

    shape = "unknown"
    if len(contours) > 0:
        cnt = max(contours, key=cv2.contourArea)
        approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
        v = len(approx)

        if v == 3:
            shape = "triangle"
        elif v == 4:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = box.astype(int)
            sides = [np.linalg.norm(box[i]-box[(i+1)%4]) for i in range(4)]
            sides.sort()
            aspect = sides[0] / sides[-1]
            shape = "cube" if aspect >= 0.7 else "rectangle"
        elif v == 5:
            shape = "arch"
        else:
            if not cv2.isContourConvex(approx):
                shape = "arch"
            else:
                area_ratio = cv2.contourArea(cnt) / (cv2.boundingRect(cnt)[2] * cv2.boundingRect(cnt)[3])
                shape = "half-circle" if area_ratio < 0.7 else "cylinder"

    b, g, r = cv2.split(img[:, :, :3])
    polished = cv2.merge((b, g, r, mask_filled))
    out_path = os.path.join(OUTPUT_FOLDER, f"polished_{shape}_{idx}.png")
    cv2.imwrite(out_path, polished)
    print(f"[Saved] {out_path} as {shape}")

# --- Interactive loop ---
files = [f for f in sorted(os.listdir(INPUT_FOLDER)) if f.lower().endswith('.png')]
for idx, file in enumerate(files):
    path = os.path.join(INPUT_FOLDER, file)
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] < 4:
        print(f"⚠️ Skipping {path}")
        continue

    alpha = img[:, :, 3]
    preview = cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR)
    cv2.imshow("Review Mask", preview)
    print(f"[{idx+1}/{len(files)}] Reviewing {file}")
    print("Press 's' = save as polished, 'r' = repair arch, 'q' = quit")

    key = cv2.waitKey(0) & 0xFF

    if key == ord('s'):
        clean_and_classify(path, idx)
    elif key == ord('r'):
        repair_arch(path, idx)
    elif key == ord('q'):
        print("👋 Exiting review.")
        break

cv2.destroyAllWindows()

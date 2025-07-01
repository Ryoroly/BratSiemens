import cv2
import numpy as np
import os

INPUT_FOLDER = "my_photos"
OUTPUT_FOLDER = "p-my_photos"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def soften_shadows_but_keep_color(img):
    # Convert to HSV to separate brightness from color
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Estimate background illumination using morphological closing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    background = cv2.morphologyEx(v, cv2.MORPH_CLOSE, kernel)

    # Avoid division by zero
    background = np.maximum(background, 1)

    # Normalize value channel by background (soft division)
    v_float = v.astype(np.float32)
    bg_float = background.astype(np.float32)
    corrected_v = (v_float / bg_float) * 128  # scale to midrange brightness

    # Clip and convert back to uint8
    corrected_v = np.clip(corrected_v, 0, 255).astype(np.uint8)

    # Merge corrected V back into HSV and convert to BGR
    corrected_hsv = cv2.merge([h, s, corrected_v])
    corrected_bgr = cv2.cvtColor(corrected_hsv, cv2.COLOR_HSV2BGR)
    return corrected_bgr

# Process all supported images
image_files = [
    f for f in os.listdir(INPUT_FOLDER)
    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
]

if not image_files:
    print("No images found in 'my_photos'.")
    exit()

for filename in image_files:
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    img = cv2.imread(input_path)
    if img is None:
        print(f"Could not read: {filename}")
        continue

    result = soften_shadows_but_keep_color(img)
    cv2.imwrite(output_path, result)
    print(f"Processed and saved: {filename}")

print("Done.")

import cv2
import numpy as np
import os
import json
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

CONFIG_FILE = "yellow_tone_removal_hsv.json"

if os.path.exists(CONFIG_FILE):
    hsv_config = json.load(open(CONFIG_FILE))
else:
    hsv_config = {
        "lh": 20, "ls": 100, "lv": 100,
        "uh": 35, "us": 255, "uv": 255
    }

def nothing(x): pass

def process_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] < 4:
        print(f"⚠️ Could not load or invalid image: {image_path}")
        return

    cv2.namedWindow("Mask Tuner")
    for k, max_val in [("lh", 179), ("ls", 255), ("lv", 255), ("uh", 179), ("us", 255), ("uv", 255)]:
        cv2.createTrackbar(k, "Mask Tuner", hsv_config[k], max_val, nothing)

    bgr = img[:, :, :3]
    alpha = img[:, :, 3]
    hsv_img = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    while True:
        for k in hsv_config:
            hsv_config[k] = cv2.getTrackbarPos(k, "Mask Tuner")

        lower = np.array([hsv_config["lh"], hsv_config["ls"], hsv_config["lv"]])
        upper = np.array([hsv_config["uh"], hsv_config["us"], hsv_config["uv"]])

        mask = cv2.inRange(hsv_img, lower, upper)
        mask_inv = cv2.bitwise_not(mask)

        new_bgr = cv2.bitwise_and(bgr, bgr, mask=mask_inv)
        new_alpha = cv2.bitwise_and(alpha, alpha, mask=mask_inv)
        result = cv2.merge((new_bgr[:, :, 0], new_bgr[:, :, 1], new_bgr[:, :, 2], new_alpha))

        preview = cv2.hconcat([
            cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(new_alpha, cv2.COLOR_GRAY2BGR)
        ])
        preview = cv2.resize(preview, (min(1200, preview.shape[1]),
                                       int(preview.shape[0] * (min(1200, preview.shape[1])/preview.shape[1]))))
        cv2.imshow("Mask Tuner", preview)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('s'):
            cv2.imwrite(image_path, result)
            with open(CONFIG_FILE, "w") as f:
                json.dump(hsv_config, f, indent=2)
            print(f"[Saved] {image_path}")
            break
        elif key == ord('q'):
            print("👋 Exiting without saving.")
            break

    cv2.destroyAllWindows()

# --- Tkinter DnD UI ---
def on_drop(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        if file.lower().endswith('.png'):
            process_image(file)
        else:
            print(f"⚠️ Skipping non-PNG: {file}")

root = TkinterDnD.Tk()
root.title("Drag & Drop PNG for Yellow Tone Removal")
root.geometry("600x200")
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

label = tk.Label(root, text="💡 Drag & drop a PNG file here\nPress 's' in the OpenCV window to save, 'q' to quit", font=("Arial", 14))
label.pack(expand=True)

root.mainloop()

import cv2
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# === CONFIG ===
USE_PI_CAMERA = False  # 🔁 Setează True când ești pe Raspberry Pi cu camera Pi

# === CLASE DE FORME ===
classes = {
    "triangle": 0, "rectangle": 1, "arch": 2,
    "half-circle": 3, "cylinder": 4, "cube": 5
}

output_dir = "dataset_debug"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)

# === FUNCȚIE DE DETECȚIE ===
def detect_shapes_and_label(frame):
    labeled_objects = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 300:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
        vertices = len(approx)
        x, y, w, h = cv2.boundingRect(contour)

        shape_label = "unidentified"
        if vertices == 3:
            shape_label = "triangle"
        elif vertices == 4:
            aspect_ratio = w / float(h)
            shape_label = "cube" if 0.95 <= aspect_ratio <= 1.05 else "rectangle"
        elif vertices == 5:
            shape_label = "arch"
        else:
            if not cv2.isContourConvex(approx):
                shape_label = "arch"
            else:
                fill_ratio = area / float(w * h)
                shape_label = "half-circle" if fill_ratio < 0.7 else "cylinder"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, shape_label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        H, W = frame.shape[:2]
        cx, cy = x + w/2, y + h/2
        labeled_objects.append((classes[shape_label], cx/W, cy/H, w/W, h/H))

    return frame, labeled_objects

# === FUNCȚIE DE SALVARE ===
def save_frame_and_labels(frame, labels):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(output_dir, "images", f"{timestamp}.jpg")
    label_path = os.path.join(output_dir, "labels", f"{timestamp}.txt")
    cv2.imwrite(img_path, frame)
    with open(label_path, "w") as f:
        for cls_id, cx, cy, w, h in labels:
            f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
    print(f"[SALVAT] {img_path} + {label_path}")

# === MAIN ===
if USE_PI_CAMERA:
    # ======== CAMERA PI (Pe Raspberry Pi) =========
    from picamera2 import Picamera2
    import time
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
    picam2.preview_configuration.main.format = "BGR888"
    picam2.configure("preview")
    picam2.start()
    time.sleep(2)

    while True:
        frame = picam2.capture_array()
        processed_frame, labels = detect_shapes_and_label(frame)
        cv2.imshow("Shape Detection - Pi Camera", processed_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("c"):
            save_frame_and_labels(frame, labels)
        elif key == ord("q"):
            break
    cv2.destroyAllWindows()

else:
    # ======== WEBCAM LAPTOP =========
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[EROARE] Webcam-ul nu este disponibil.")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        processed_frame, labels = detect_shapes_and_label(frame)
        # cv2.imshow("Shape Detection - Webcam", processed_frame)
        plt.imshow(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB))
        plt.title("Shape Detection - Webcam")
        plt.axis("off")
        plt.show()
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord("c"):
            save_frame_and_labels(frame, labels)
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

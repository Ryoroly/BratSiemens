import streamlit as st
import cv2
import numpy as np
import os

# --- CONFIG ---
base_dir = os.path.dirname(os.path.abspath(__file__))
TEMP_ROOT = os.path.join(base_dir, "temp")
APP1_FOLDER = os.path.join(TEMP_ROOT, "app1_extract_selector")
APP2_FOLDER = os.path.join(TEMP_ROOT, "app2_extract_selector")
OBJECTS_ROOT = os.path.join(APP1_FOLDER, "objects")

# Sidebar: App title
st.sidebar.title("App 2: Shape Classifier & Saver")

# Ensure objects directory exists
if not os.path.isdir(OBJECTS_ROOT):
    st.sidebar.error("No extraction runs found. Run App 1 first.")
    st.stop()

# List runs
run_folders = sorted([
    d for d in os.listdir(OBJECTS_ROOT)
    if os.path.isdir(os.path.join(OBJECTS_ROOT, d))
])
if not run_folders:
    st.sidebar.error("No extraction runs found. Run App 1 first.")
    st.stop()

selected_run = st.sidebar.selectbox("Select extraction run", run_folders)
obj_dir = os.path.join(OBJECTS_ROOT, selected_run)

# Prepare output directory for saving classified objects
CLASSIFIED_ROOT = os.path.join(APP2_FOLDER)
# create subfolder for this run
OUTPUT_CLASS_DIR = os.path.join(CLASSIFIED_ROOT, selected_run)

# Load object images
images = sorted([f for f in os.listdir(obj_dir) if f.lower().endswith('.png')])
if not images:
    st.sidebar.error("No PNG objects in selected run.")
    st.stop()

# Shape classification

def classify_shape(obj_bgra):
    mask = obj_bgra[:, :, 3]
    kernel = np.ones((5,5), np.uint8)
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return "unknown"
    cnt = max(cnts, key=cv2.contourArea)
    approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
    v = len(approx)
    if v == 3:
        return "triangle"
    elif v == 4:
        x, y, w, h = cv2.boundingRect(approx)
        ratio = float(w) / h
        return "square" if 0.95 <= ratio <= 1.05 else "rectangle"
    elif v == 5:
        return "pentagon"
    else:
        area = cv2.contourArea(cnt)
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        circle_area = np.pi * (radius ** 2)
        return "circle" if abs(area - circle_area) < 0.1 * circle_area else "unknown"

# Display classified images
st.title("Detected & Classified Shapes")
cols_per_row = 3
for i in range(0, len(images), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, fname in enumerate(images[i:i+cols_per_row]):
        path = os.path.join(obj_dir, fname)
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        preview = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        shape = classify_shape(img)
        cols[j].image(preview, caption=f"{fname}\n-> {shape}", use_container_width=True)

# Save classified objects
def save_classified():
    os.makedirs(OUTPUT_CLASS_DIR, exist_ok=True)
    count = 0
    for fname in images:
        path = os.path.join(obj_dir, fname)
        obj = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        shape = classify_shape(obj)
        out_name = f"{os.path.splitext(fname)[0]}_{shape}.png"
        out_path = os.path.join(OUTPUT_CLASS_DIR, out_name)
        cv2.imwrite(out_path, obj)
        count += 1
    st.success(f"Saved {count} classified objects to {OUTPUT_CLASS_DIR}")

if st.sidebar.button("Save classified objects"):
    save_classified()

st.sidebar.info(f"Saving to: {OUTPUT_CLASS_DIR}")

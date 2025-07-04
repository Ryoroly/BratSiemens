import streamlit as st
import cv2
import numpy as np
import os
from datetime import datetime
import shutil

# --- CONFIG ---
base_dir = os.path.dirname(os.path.abspath(__file__))
TEMP_ROOT = os.path.join(base_dir, "temp")
APP2_SIMPLE = os.path.join(TEMP_ROOT, "app2_shape_classifier")
OBJECTS_ROOT = os.path.join(base_dir, "temp", "app1_extract_selector", "objects")

# Ensure objects directory exists
if not os.path.isdir(OBJECTS_ROOT):
    st.error("No extracted objects found. Run App 1 first.")
    st.stop()

# Sidebar: select run
st.sidebar.title("App 2: Detect & Save")
runs = sorted(d for d in os.listdir(OBJECTS_ROOT) if os.path.isdir(os.path.join(OBJECTS_ROOT, d)))
if not runs:
    st.sidebar.error("No extraction runs available.")
    st.stop()
selected_run = st.sidebar.selectbox("Select extraction run", runs)
obj_dir = os.path.join(OBJECTS_ROOT, selected_run)

# List PNGs
images = sorted(f for f in os.listdir(obj_dir) if f.lower().endswith('.png'))
if not images:
    st.info("No PNG objects found in selected run.")
    st.stop()

# Shape classification
def classify_shape(obj):
    mask = obj[:, :, 3]
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
        x,y,w,h = cv2.boundingRect(approx)
        return "square" if 0.95 <= w/h <= 1.05 else "rectangle"
    else:
        area = cv2.contourArea(cnt)
        (x,y), r = cv2.minEnclosingCircle(cnt)
        circle_area = np.pi * (r**2)
        return "circle" if abs(area - circle_area) < 0.1 * circle_area else "unknown"

# Display detections
st.title("Detected Shapes")
cols = st.columns(3)
for idx, fname in enumerate(images):
    img = cv2.imread(os.path.join(obj_dir, fname), cv2.IMREAD_UNCHANGED)
    rgba = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
    shape = classify_shape(img)
    col = cols[idx % 3]
    col.image(rgba, caption=f"{fname}\n-> {shape}", use_container_width=True)

# Save callback
def save_all():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(APP2_SIMPLE, "saved", f"{selected_run}_{ts}")
    os.makedirs(out_dir, exist_ok=True)
    for fname in images:
        src = os.path.join(obj_dir, fname)
        dst = os.path.join(out_dir, fname)
        shutil.copy(src, dst)
    st.success(f"Saved {len(images)} objects to {out_dir}")

if st.sidebar.button("Save All Objects"):
    save_all()
st.sidebar.info("Click to copy all detected objects to a timestamped folder.")

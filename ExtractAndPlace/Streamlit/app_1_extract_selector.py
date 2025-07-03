import streamlit as st
import cv2
import numpy as np
import os
import json
from datetime import datetime

# --- CONFIG ---
base_dir = os.path.dirname(os.path.abspath(__file__))
RAWOBJ_FOLDER = os.path.join(base_dir, "rawObj")
TEMP_ROOT = os.path.join(base_dir, "temp")
APP_NAME = "app1_extract_selector"
APP_FOLDER = os.path.join(TEMP_ROOT, APP_NAME)
CONFIG_FILE = os.path.join(APP_FOLDER, "threshold_config.json")
OUTPUT_FOLDER = os.path.join(APP_FOLDER, "objects")

# Ensure directories exist
os.makedirs(RAWOBJ_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load or init HSV thresholds
if os.path.exists(CONFIG_FILE):
    try:
        hsv = json.load(open(CONFIG_FILE))
    except Exception:
        hsv = {"lh":0,"ls":0,"lv":0,"uh":179,"us":255,"uv":255}
else:
    hsv = {"lh":0,"ls":0,"lv":0,"uh":179,"us":255,"uv":255}

# Sidebar settings
st.sidebar.title("App 1: Mask Selector Settings")
subfolders = [d for d in os.listdir(RAWOBJ_FOLDER) if os.path.isdir(os.path.join(RAWOBJ_FOLDER, d))]
if not subfolders:
    st.sidebar.warning(f"No folders in rawObj: {RAWOBJ_FOLDER}")
    st.sidebar.info("Please add subfolders under rawObj and restart.")
    st.stop()
selected_set = st.sidebar.selectbox("Select raw object folder", subfolders)
input_folder = os.path.join(RAWOBJ_FOLDER, selected_set)

st.sidebar.subheader("HSV Thresholds")
lh = st.sidebar.slider("Low Hue", 0, 179, hsv.get("lh", 0))
ls = st.sidebar.slider("Low Sat", 0, 255, hsv.get("ls", 0))
lv = st.sidebar.slider("Low Val", 0, 255, hsv.get("lv", 0))
uh = st.sidebar.slider("High Hue", 0, 179, hsv.get("uh", 179))
us = st.sidebar.slider("High Sat", 0, 255, hsv.get("us", 255))
uv = st.sidebar.slider("High Val", 0, 255, hsv.get("uv", 255))
if st.sidebar.button("Save thresholds", key="save_thresh"):
    os.makedirs(APP_FOLDER, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"lh": lh, "ls": ls, "lv": lv, "uh": uh, "us": us, "uv": uv}, f)
    st.sidebar.success("Thresholds saved.")

# Main title
st.title("Interactive Mask Selector (App 1)")
st.write(f"**Raw object set:** `{selected_set}` ({len(os.listdir(input_folder))} images)")

# Load images
valid_ext = (".jpg", ".jpeg", ".png", ".bmp")
image_paths = sorted([
    os.path.join(input_folder, f)
    for f in os.listdir(input_folder)
    if f.lower().endswith(valid_ext)
])
if not image_paths:
    st.info("No images found.")
    st.stop()

# Initialize session index
if 'idx' not in st.session_state:
    st.session_state.idx = 0

# Navigation buttons
col_nav1, _, col_nav3 = st.columns([1, 2, 1])
with col_nav1:
    if st.button("←", key="prev"):
        st.session_state.idx = max(0, st.session_state.idx - 1)
with col_nav3:
    if st.button("→", key="next"):
        st.session_state.idx = min(len(image_paths) - 1, st.session_state.idx + 1)

# Current image index
idx = st.session_state.idx
img_path = image_paths[idx]
st.write(f"### {os.path.basename(img_path)} ({idx+1}/{len(image_paths)})")

# Read and process image & mask
img = cv2.imread(img_path)
hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower = np.array([lh, ls, lv])
upper = np.array([uh, us, uv])
mask = cv2.inRange(hsv_img, lower, upper)
kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

# Extract object crops
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
obj_images = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    crop_bgr = img[y:y+h, x:x+w]
    crop_mask = mask[y:y+h, x:x+w]
    # Convert to RGBA and use mask as alpha
    crop_rgba = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGBA)
    crop_rgba[:, :, 3] = crop_mask
    obj_images.append(crop_rgba)

# Display original & mask
col_orig, col_mask = st.columns(2)
col_orig.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
col_mask.image(mask, caption="Mask", use_container_width=True)

# Display object grid
st.write("### Extracted Objects (transparent PNGs)")
if obj_images:
    for i in range(0, len(obj_images), 3):
        cols = st.columns(3)
        for j, obj_rgba in enumerate(obj_images[i:i+3]):
            cols[j].image(obj_rgba, caption=f"Obj {i+j}", use_container_width=True)
else:
    st.info("No objects detected to extract.")

# Save button with callback to handle saving and advancing
def save_and_advance(img_path, lh, ls, lv, uh, us, uv, output_folder):
    # create timestamped folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(output_folder, timestamp)
    os.makedirs(run_folder, exist_ok=True)
    # read image and generate mask
    img = cv2.imread(img_path)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([lh, ls, lv])
    upper = np.array([uh, us, uv])
    mask = cv2.inRange(hsv_img, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # save each contour crop
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    base = os.path.splitext(os.path.basename(img_path))[0]
    count = 0
    for k, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        obj = img[y:y+h, x:x+w]
        out_path = os.path.join(run_folder, f"{base}_obj_{k}.png")
        cv2.imwrite(out_path, obj)
        count += 1
    st.success(f"Saved {count} objects to {run_folder}")
    # advance to next image
    if st.session_state.idx < len(image_paths) - 1:
        st.session_state.idx += 1

# Button invoking callback
st.button(
    "Save extracted objects",
    key="save_objs",
    on_click=save_and_advance,
    args=(img_path, lh, ls, lv, uh, us, uv, OUTPUT_FOLDER),
)

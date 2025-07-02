"""
Streamlit app to visualise YOLO dataset splits.
Run with:
    streamlit run dataset_visualizer.py
"""
import os
from PIL import Image, ImageDraw
import streamlit as st

# --- Configuration ---
st.set_page_config(page_title="Dataset Visualizer", layout="wide")
dataset_dir = st.sidebar.text_input("Dataset root folder", "dataset")
split = st.sidebar.selectbox("Select split", ["train", "val"])

# --- Paths ---
img_dir = os.path.join(dataset_dir, split, "images")
lbl_dir = os.path.join(dataset_dir, split, "labels")

# --- List images ---
try:
    images = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png'))])
except FileNotFoundError:
    st.error(f"Directory not found: {img_dir}")
    st.stop()

if not images:
    st.warning(f"No images in {img_dir}")
    st.stop()

# --- Sidebar navigation ---
view_mode = st.sidebar.radio("View mode", ["Single", "Gallery"])

if view_mode == "Single":
    # Navigation arrows and index
    index = st.sidebar.number_input("Image index", min_value=0, max_value=len(images)-1, value=0, step=1)
    prev_col, next_col = st.sidebar.columns(2)
    if prev_col.button("⬅️ Previous"):
        index = max(index - 1, 0)
    if next_col.button("Next ➡️"):
        index = min(index + 1, len(images)-1)
    selected = images[index]
    st.sidebar.write(f"{index + 1} / {len(images)}")
else:
    # Gallery view: thumbnails
    cols = st.columns(4)
    selected = None
    for i, img_name in enumerate(images):
        col = cols[i % 4]
        with col:
            thumbnail = Image.open(os.path.join(img_dir, img_name)).resize((160, 140))
            if st.button(img_name, key=f"btn_{i}"):
                selected = img_name
                view_mode = "Single"
    if selected is None:
        selected = images[0]

# --- Load selected image ---
img_path = os.path.join(img_dir, selected)
lbl_path = os.path.join(lbl_dir, selected.rsplit('.', 1)[0] + '.txt')

# --- Load and draw ---
image = Image.open(img_path).convert("RGB")
w, h = image.size

draw = ImageDraw.Draw(image)
if os.path.exists(lbl_path):
    with open(lbl_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls_id, x_c, y_c, bw, bh = map(float, parts)
            x_c, y_c, bw, bh = x_c * w, y_c * h, bw * w, bh * h
            x0, y0 = x_c - bw/2, y_c - bh/2
            x1, y1 = x_c + bw/2, y_c + bh/2
            draw.rectangle([x0, y0, x1, y1], outline="red", width=2)
            draw.text((x0, y0 - 10), str(int(cls_id)), fill="red")
else:
    st.warning("Missing label file for selected image.")

# --- Display ---
st.image(image, caption=f"{split}/{selected}", use_container_width=True)

# --- Info ---
st.sidebar.markdown("---")
st.sidebar.write(f"Image size: {w}×{h}")
st.sidebar.write(f"Labels found: {os.path.exists(lbl_path)}")

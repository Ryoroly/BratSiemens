import streamlit as st
import cv2
import numpy as np
import os
from datetime import datetime

# --- CONFIG ---
base_dir = os.path.dirname(os.path.abspath(__file__))
TEMP_ROOT = os.path.join(base_dir, "temp")
APP1_FOLDER = os.path.join(TEMP_ROOT, "app1_extract_selector")
APP2_FOLDER = os.path.join(TEMP_ROOT, "app2_shape_classifier")
OBJECTS_ROOT = os.path.join(APP1_FOLDER, "objects")

# Sidebar Title
st.sidebar.title("App 2: Shape Classifier & Renamer")

# Ensure objects directory exists
if not os.path.isdir(OBJECTS_ROOT):
    st.sidebar.error("No extraction runs found. Run App 1 first.")
    st.stop()

# Select extraction run
run_folders = sorted(
    d for d in os.listdir(OBJECTS_ROOT)
    if os.path.isdir(os.path.join(OBJECTS_ROOT, d))
)
selected_run = st.sidebar.selectbox("Select extraction run", run_folders)
obj_dir = os.path.join(OBJECTS_ROOT, selected_run)

# List PNG files
def list_pngs(folder):
    return [f for f in sorted(os.listdir(folder)) if f.lower().endswith('.png')]

def classify_shape(obj):
    mask = obj[:, :, 3]  # Alpha channel
    kern = np.ones((5, 5), np.uint8)
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kern)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kern)

    cnts, hierarchy = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts or hierarchy is None:
        return "unknown"

    hierarchy = hierarchy[0]  # shape: (num_contours, 4)
    outer_cnts = [cnts[i] for i, h in enumerate(hierarchy) if h[3] == -1]
    hole_cnts = [cnts[i] for i, h in enumerate(hierarchy) if h[3] != -1]

    if len(outer_cnts) == 1 and len(hole_cnts) == 1:
        outer = outer_cnts[0]
        inner = hole_cnts[0]

        # Check if the inner contour is fairly circular
        area = cv2.contourArea(inner)
        (x, y), r = cv2.minEnclosingCircle(inner)
        circle_area = np.pi * r * r
        circularity_error = abs(area - circle_area) / circle_area

        # Also check placement of the hole: not too close to the edge
        ox, oy, ow, oh = cv2.boundingRect(outer)
        cx, cy, cr = x, y, r
        if circularity_error < 0.25 and ox + 0.2*ow < cx < ox + 0.8*ow:
            return "arch"

    # Fallback to classic logic
    cnt = max(cnts, key=cv2.contourArea)
    approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
    v = len(approx)

    if v == 3:
        return "triangle"
    if v == 4:
        x, y, w, h = cv2.boundingRect(approx)
        return "square" if 0.95 <= w / float(h) <= 1.05 else "rectangle"
    if v == 5:
        return "pentagon"

    # Circle fallback
    area = cv2.contourArea(cnt)
    (x, y), r = cv2.minEnclosingCircle(cnt)
    return "circle" if abs(area - np.pi * r * r) < 0.1 * np.pi * r * r else "unknown"

# Shapes order
shapes = ["triangle", "square", "rectangle", "pentagon", "circle", "arch", "unknown"]

# Load and classify images
files = list_pngs(obj_dir)
if not files:
    st.error("No PNG images found in selected run.")
    st.stop()
items = []
for fname in files:
    img = cv2.imread(os.path.join(obj_dir, fname), cv2.IMREAD_UNCHANGED)
    items.append({"file": fname, "image": img, "shape": classify_shape(img)})

# Sort items by detected shape
sorted_items = sorted(items, key=lambda x: shapes.index(x['shape']))

# Initialize selection state
if 'to_rename' not in st.session_state:
    st.session_state.to_rename = []

# Define batch rename callback
def do_batch_rename():
    target = st.session_state.get('common_shape')
    # Determine the next index for the target based on existing files
    existing = [f for f in os.listdir(obj_dir) if f.startswith(f"{target}_") and f.lower().endswith('.png')]
    # Extract numeric indices
    indices = []
    for f in existing:
        try:
            idx_str = f[len(target) + 1:-4]
            indices.append(int(idx_str))
        except ValueError:
            continue
    next_idx = max(indices) if indices else 0
    # Rename selected files sequentially, avoiding collisions
    for orig in st.session_state.to_rename:
        next_idx += 1
        src = os.path.join(obj_dir, orig)
        dst_name = f"{target}_{next_idx:04d}.png"
        dst = os.path.join(obj_dir, dst_name)
        if os.path.exists(src) and src != dst:
            # Ensure destination does not exist
            if os.path.exists(dst):
                st.warning(f"Skipping rename for {orig}: {dst_name} already exists")
            else:
                os.rename(src, dst)
    # Clear selection and force UI refresh
    st.session_state.to_rename = []
    try:
        st.experimental_rerun()
    except Exception:
        pass

# Main UI
st.title("Shapes & Batch Rename")
cols = 3

# Display sorted images with selection checkboxes
for i in range(0, len(sorted_items), cols):
    row = sorted_items[i:i+cols]
    cols_ui = st.columns(cols)
    for col_ui, item in zip(cols_ui, row):
        fn = item['file']
        img = cv2.cvtColor(item['image'], cv2.COLOR_BGRA2RGBA)
        col_ui.image(img, caption=f"{fn}\n-> {item['shape']}", use_container_width=True)
        selected = col_ui.checkbox("Select to rename", key=f"sel_{fn}")
        if selected and fn not in st.session_state.to_rename:
            st.session_state.to_rename.append(fn)
        if not selected and fn in st.session_state.to_rename:
            st.session_state.to_rename.remove(fn)

# Batch rename controls
to_rename = st.session_state.to_rename
if to_rename:
    st.write(f"**{len(to_rename)} files selected for rename**: {to_rename}")
    st.selectbox("Rename all selected as:", shapes, key="common_shape")
    st.button("Apply Batch Rename", on_click=do_batch_rename)
else:
    st.info("Select images above to enable batch rename.")

# Automatically show sorted groups after rename
for shp in shapes:
    group = [it for it in sorted_items if it['shape'] == shp]
    if group:
        st.subheader(shp.capitalize())
        for i in range(0, len(group), cols):
            cols_ui = st.columns(cols)
            for col_ui, it in zip(cols_ui, group[i:i+cols]):
                img = cv2.cvtColor(it['image'], cv2.COLOR_BGRA2RGBA)
                col_ui.image(img, caption=it['file'], use_container_width=True)

# Save classified images to timestamped folder
def save_classified():
    # Re-scan directory to catch renamed files
    files_now = list_pngs(obj_dir)
    # Re-classify based on updated filenames
    items_now = []
    for fname in files_now:
        img = cv2.imread(os.path.join(obj_dir, fname), cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        shape = classify_shape(img)
        items_now.append({"file": fname, "image": img, "shape": shape})
    # Sort items by detected shape
    items_now_sorted = sorted(items_now, key=lambda x: shapes.index(x['shape']))
    # Prepare output folder
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(APP2_FOLDER, "classified_objects", f"{selected_run}_{ts}")
    os.makedirs(out_dir, exist_ok=True)
    # Save each image with its current name/shape mapping
    for item in items_now_sorted:
        shp = item['shape']
        base_name = os.path.splitext(item['file'])[0]
        outfile = f"{base_name}.png"
        cv2.imwrite(os.path.join(out_dir, outfile), item['image'])
    st.sidebar.success(f"Saved {len(items_now_sorted)} images to {out_dir}")

st.sidebar.button("Save Classified Images", on_click=save_classified)
st.sidebar.info("Use above to view, select, rename, and save images.")

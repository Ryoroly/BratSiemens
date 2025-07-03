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

# Sidebar: App title
st.sidebar.title("App 2: Shape Classifier & Renamer")

# Ensure objects directory exists
if not os.path.isdir(OBJECTS_ROOT):
    st.sidebar.error("No extraction runs found. Run App 1 first.")
    st.stop()

# Select run folder
run_folders = sorted([
    d for d in os.listdir(OBJECTS_ROOT)
    if os.path.isdir(os.path.join(OBJECTS_ROOT, d))
])
if not run_folders:
    st.sidebar.error("No extraction runs found. Run App 1 first.")
    st.stop()
selected_run = st.sidebar.selectbox("Select extraction run", run_folders)
obj_dir = os.path.join(OBJECTS_ROOT, selected_run)

# Utility: list PNGs
list_pngs = lambda d: sorted([f for f in os.listdir(d) if f.lower().endswith('.png')])

# Classification logic
def classify_shape(obj):
    mask = obj[:, :, 3]
    kern = np.ones((5,5), np.uint8)
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kern)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kern)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return "unknown"
    cnt = max(cnts, key=cv2.contourArea)
    approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
    v = len(approx)
    if v == 3:
        return "triangle"
    if v == 4:
        x,y,w,h = cv2.boundingRect(approx)
        return "square" if 0.95 <= w/float(h) <= 1.05 else "rectangle"
    if v == 5:
        return "pentagon"
    area = cv2.contourArea(cnt)
    (x,y),r = cv2.minEnclosingCircle(cnt)
    return "circle" if abs(area - np.pi*r*r) < 0.1*np.pi*r*r else "unknown"

# Shapes order
shapes = ["triangle", "square", "rectangle", "pentagon", "circle", "unknown"]

# Load and classify images
image_files = list_pngs(obj_dir)
if not image_files:
    st.sidebar.error("No PNG objects in selected run.")
    st.stop()
items = [
    {"file": f, "image": cv2.imread(os.path.join(obj_dir,f), cv2.IMREAD_UNCHANGED),
     "shape": classify_shape(cv2.imread(os.path.join(obj_dir,f), cv2.IMREAD_UNCHANGED))}
    for f in image_files
]
# Sort items by detected shape
sorted_items = sorted(items, key=lambda x: shapes.index(x['shape']))

# Initialize selection
if 'to_rename' not in st.session_state:
    st.session_state.to_rename = []

# Main interface
st.title("Shapes & Batch Rename")
cols = 3
for i in range(0, len(sorted_items), cols):
    cols_ui = st.columns(cols)
    for col_ui, item in zip(cols_ui, sorted_items[i:i+cols]):
        fn = item['file']
        img = item['image']
        preview = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        col_ui.image(preview, caption=f"{fn}\n-> {item['shape']}", use_container_width=True)
        sel = col_ui.checkbox("Select to rename", key=f"sel_{fn}")
        if sel and fn not in st.session_state.to_rename:
            st.session_state.to_rename.append(fn)
        if not sel and fn in st.session_state.to_rename:
            st.session_state.to_rename.remove(fn)

# Batch rename callback
def do_batch_rename():
    target = st.session_state.get('common_shape')
    existing = [f for f in os.listdir(obj_dir) if f.startswith(target + '_')]
    seq = len(existing)
    for orig in list(st.session_state.to_rename):
        seq += 1
        src = os.path.join(obj_dir, orig)
        dst = os.path.join(obj_dir, f"{target}_{seq:04d}.png")
        try:
            os.rename(src, dst)
        except Exception as e:
            st.error(f"Failed to rename {orig}: {e}")
    # Clear state and rerun
    for orig in st.session_state.to_rename:
        sel_key = f"sel_{orig}"
        if sel_key in st.session_state:
            del st.session_state[sel_key]
    st.session_state.to_rename = []
    st.experimental_rerun()

# Show selection and rename controls
to_rename = st.session_state.to_rename
if to_rename:
    st.write(f"**{len(to_rename)} files selected for rename:** {to_rename}")
    st.selectbox("Rename all selected as:", shapes, key='common_shape')
    st.button("Apply Batch Rename", on_click=do_batch_rename)
else:
    st.info("Select files above to enable rename.")

# Automatically display sorted groups below
total = len(sorted_items)
st.write(f"### All {total} images sorted by shape:")
for shp in shapes:
    group = [item for item in sorted_items if item['shape'] == shp]
    if group:
        st.subheader(shp.capitalize())
        for i in range(0, len(group), cols):
            cols_ui = st.columns(cols)
            for col_ui, item in zip(cols_ui, group[i:i+cols]):
                pr = cv2.cvtColor(item['image'], cv2.COLOR_BGRA2RGBA)
                col_ui.image(pr, caption=item['file'], use_container_width=True)

# Save classified images
def save_classified():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outd = os.path.join(APP2_FOLDER, "classified_objects", f"{selected_run}_{ts}")
    os.makedirs(outd, exist_ok=True)
    counts = {}
    total_saved = 0
    for item in sorted_items:
        shp = item['shape']
        counts.setdefault(shp, 0)
        counts[shp] += 1
        name = f"{shp}_{counts[shp]:04d}.png"
        cv2.imwrite(os.path.join(outd, name), item['image'])
        total_saved += 1
    st.sidebar.success(f"Saved {total_saved} images to {outd}")

st.sidebar.button("Save classified images", on_click=save_classified)
st.sidebar.info("Use main view to select, rename, and view sorted images automatically.")
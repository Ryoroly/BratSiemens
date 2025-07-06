import streamlit as st
import cv2
import numpy as np
import os
import json
from datetime import datetime

# --- CONFIG ---
def initialize_directories():
    """Initialize and create necessary directories."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    RAWOBJ_FOLDER = os.path.join(base_dir, "rawObj")
    TEMP_ROOT = os.path.join(base_dir, "temp")
    APP_NAME = "app1_extract_selector"
    APP_FOLDER = os.path.join(TEMP_ROOT, APP_NAME)
    CONFIG_FILE = os.path.join(APP_FOLDER, "threshold_config.json")
    OUTPUT_ROOT = os.path.join(APP_FOLDER, "objects")
    
    # Ensure base directories exist
    os.makedirs(RAWOBJ_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    return {
        'rawobj': RAWOBJ_FOLDER,
        'app_folder': APP_FOLDER,
        'config_file': CONFIG_FILE,
        'output_root': OUTPUT_ROOT
    }

def load_hsv_config(config_file):
    """Load HSV configuration from file or return defaults."""
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {"lh":0, "ls":0, "lv":0, "uh":179, "us":255, "uv":255}

def save_hsv_config(config_file, hsv_values):
    """Save HSV configuration to file."""
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(hsv_values, f)

def process_image_mask(img, hsv_values):
    """Process image and return mask for object detection."""
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([hsv_values["lh"], hsv_values["ls"], hsv_values["lv"]])
    upper = np.array([hsv_values["uh"], hsv_values["us"], hsv_values["uv"]])
    mask = cv2.inRange(hsv_img, lower, upper)
    
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    return mask

def extract_objects(img, mask):
    """Extract objects from image using mask."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    obj_images = []
    
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        crop_bgr = img[y:y+h, x:x+w]
        crop_mask = mask[y:y+h, x:x+w]
        rgba = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = crop_mask
        obj_images.append(rgba)
    
    return obj_images

def save_objects(img_path, objects, output_folder):
    """Save extracted objects as PNG files."""
    os.makedirs(output_folder, exist_ok=True)
    count = 0
    
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    for k, obj_rgba in enumerate(objects):
        out_path = os.path.join(output_folder, f"{base_name}_obj_{k}.png")
        cv2.imwrite(out_path, obj_rgba)
        count += 1
    
    return count

def save_and_advance():
    """Save objects and advance to next image."""
    # Regenerate processing for current image
    img = cv2.imread(st.session_state.current_img_path)
    mask = process_image_mask(img, st.session_state.current_hsv)
    objects = extract_objects(img, mask)
    
    count = save_objects(st.session_state.current_img_path, objects, st.session_state.output_folder)
    st.success(f"S-au salvat {count} obiecte în {st.session_state.output_folder}")
    
    # Advance to next image
    if st.session_state.idx < len(st.session_state.image_paths) - 1:
        st.session_state.idx += 1

# Initialize directories
paths = initialize_directories()
hsv_config = load_hsv_config(paths['config_file'])

# Sidebar: settings
st.sidebar.title("Setări Selector Mască")

# Choose raw object set
subfolders = [d for d in os.listdir(paths['rawobj']) if os.path.isdir(os.path.join(paths['rawobj'], d))]
if not subfolders:
    st.sidebar.warning(f"Nu există foldere în rawObj: {paths['rawobj']}")
    st.sidebar.info("Adaugă subfoldere în rawObj și repornește aplicația.")
    st.stop()

selected_set = st.sidebar.selectbox("Alege folderul cu obiecte", subfolders)
input_folder = os.path.join(paths['rawobj'], selected_set)

# Reset timestamp if folder changes
if 'last_set' not in st.session_state or st.session_state.last_set != selected_set:
    st.session_state.run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.last_set = selected_set

# Timestamp for this run
run_ts = st.session_state.run_ts
OUTPUT_FOLDER = os.path.join(paths['output_root'], f"{selected_set}_{run_ts}")

# HSV threshold controls
st.sidebar.subheader("Praguri HSV")
lh = st.sidebar.slider("Nuanță Minimă", 0, 179, hsv_config.get("lh", 0))
ls = st.sidebar.slider("Saturație Minimă", 0, 255, hsv_config.get("ls", 0))
lv = st.sidebar.slider("Valoare Minimă", 0, 255, hsv_config.get("lv", 0))
uh = st.sidebar.slider("Nuanță Maximă", 0, 179, hsv_config.get("uh", 179))
us = st.sidebar.slider("Saturație Maximă", 0, 255, hsv_config.get("us", 255))
uv = st.sidebar.slider("Valoare Maximă", 0, 255, hsv_config.get("uv", 255))

current_hsv = {"lh": lh, "ls": ls, "lv": lv, "uh": uh, "us": us, "uv": uv}

if st.sidebar.button("Salvează pragurile", key="save_thresh"):
    save_hsv_config(paths['config_file'], current_hsv)
    st.sidebar.success("Pragurile au fost salvate.")

# Main interface
st.title("Selector Interactiv de Măști")
st.write(f"**Set obiecte:** `{selected_set}` conține {len(os.listdir(input_folder))} imagini")

# Load image paths
valid_ext = (".jpg", ".jpeg", ".png", ".bmp")
image_paths = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(valid_ext)])

if not image_paths:
    st.info("Nu s-au găsit imagini.")
    st.stop()

# Initialize current index
if 'idx' not in st.session_state:
    st.session_state.idx = 0

# Store current state for save callback
st.session_state.current_hsv = current_hsv
st.session_state.image_paths = image_paths
st.session_state.output_folder = OUTPUT_FOLDER

# Navigation
col_left, _, col_right = st.columns([1,2,1])
with col_left:
    if st.button("← Anterior", key="prev"):
        st.session_state.idx = max(0, st.session_state.idx - 1)
with col_right:
    if st.button("Următor →", key="next"):
        st.session_state.idx = min(len(image_paths) - 1, st.session_state.idx + 1)

# Load current image
idx = st.session_state.idx
img_path = image_paths[idx]
st.session_state.current_img_path = img_path

st.write(f"### Imaginea {idx+1}/{len(image_paths)}: {os.path.basename(img_path)}")

# Read image and compute mask
img = cv2.imread(img_path)
mask = process_image_mask(img, current_hsv)
obj_images = extract_objects(img, mask)

# Display original & mask
col1, col2 = st.columns(2)
col1.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
col2.image(mask, caption="Mască", use_container_width=True)

# Display objects in grid of 3
st.write("### Obiecte Extrase (PNG-uri transparente)")
if obj_images:
    for i in range(0, len(obj_images), 3):
        cols = st.columns(3)
        for j, obj_bgra in enumerate(obj_images[i:i+3]):
            # convert BGRA to RGBA for correct preview colors
            preview = cv2.cvtColor(obj_bgra, cv2.COLOR_BGRA2RGBA)
            cols[j].image(preview, caption=f"Obiect {i+j+1}", use_container_width=True)
else:
    st.info("Nu există obiecte de afișat.")

# Save button
st.button(
    "Salvează obiectele extrase",
    key="save_objs",
    on_click=save_and_advance
)
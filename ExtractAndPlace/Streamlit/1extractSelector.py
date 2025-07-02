import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import shutil
import zipfile
import json

# --- CONFIG ---
CONFIG_FILE = "threshold_config.json"

def init_hsv():
    return {"lh":0, "ls":0, "lv":0, "uh":179, "us":255, "uv":255}

# Initialize HSV config in session state
if 'hsv_config' not in st.session_state:
    if os.path.exists(CONFIG_FILE):
        st.session_state.hsv_config = json.load(open(CONFIG_FILE))
    else:
        st.session_state.hsv_config = init_hsv()

# Slider max values per channel
MAX_VALS = {'lh':179, 'ls':255, 'lv':255, 'uh':179, 'us':255, 'uv':255}

# Color ranges
COLOR_RANGES = {
    "red": [((0,100,100),(10,255,255)), ((160,100,100),(179,255,255))],
    "green": [((40,50,50),(85,255,255))],
    "yellow": [((20,100,100),(35,255,255))],
    "pink": [((145,100,100),(165,255,255))],
    "light_blue": [((85,100,100),(105,255,255))],
    "orange": [((10,100,100),(20,255,255))],
    "blue": [((105,100,100),(130,255,255))]
}

# Morphology and mask utils
kernel = np.ones((5,5), np.uint8)
def apply_morph(mask):
    return cv2.morphologyEx(
        cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel),
        cv2.MORPH_CLOSE, kernel
    )
def invert_mask(mask): return cv2.bitwise_not(mask)

def gen_masks(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    masks = {}
    for name, ranges in COLOR_RANGES.items():
        m = np.zeros(img.shape[:2], np.uint8)
        for lo, hi in ranges:
            m |= cv2.inRange(hsv, np.array(lo), np.array(hi))
        masks[name] = invert_mask(apply_morph(m))
    return masks

def auto_top(masks):
    counts = {c: cv2.countNonZero(m) for c, m in masks.items()}
    top2 = [c for c, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True) if counts[c]>0][:2]
    return top2

def extract(img, mask):
    out = np.zeros_like(img)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cnts:
        if cv2.contourArea(cnt) < 300: continue
        x, y, w, h = cv2.boundingRect(cnt)
        out[y:y+h, x:x+w] = img[y:y+h, x:x+w]
    return out

# App UI
st.title("Image Mask Extractor")
uploaded = st.file_uploader("Drag & drop images", type=["png","jpg","jpeg","bmp"], accept_multiple_files=True)

if uploaded:
    # Initialize state on first run
    if 'idx' not in st.session_state:
        st.session_state.idx = 0
        tmp = tempfile.mkdtemp(prefix="temp_")
        st.session_state.tmp = tmp
        extract_dir = os.path.join(tmp, "1extractSelector")
        os.makedirs(extract_dir, exist_ok=True)
        st.session_state.extract_dir = extract_dir
        st.session_state.choice = None
    
    idx = st.session_state.idx
    files = uploaded
    # Process current image
    if idx < len(files):
        file = files[idx]
        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        st.subheader(f"Image {idx+1}/{len(files)}: {file.name}")
        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)

        masks = gen_masks(img)
        top2 = auto_top(masks)
        # Show buttons for each color + Manual
        cols = st.columns(4)
        for i, name in enumerate(list(masks.keys()) + ["Manual"]):
            if cols[i%4].button(name, key=f"btn_{idx}_{name}"):
                st.session_state.choice = name
        choice = st.session_state.choice
        mask = None

        if choice and choice != "Manual":
            mask = masks[choice]
        elif choice == "Manual":
            st.write("### Manual HSV Calibration")
            slider_cols = st.columns(6)
            for j, k in enumerate(['lh','ls','lv','uh','us','uv']):
                val = slider_cols[j].slider(k, 0, MAX_VALS[k], st.session_state.hsv_config[k], key=f"sl_{idx}_{k}")
                st.session_state.hsv_config[k] = val
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            raw = cv2.inRange(
                hsv,
                np.array([st.session_state.hsv_config['lh'], st.session_state.hsv_config['ls'], st.session_state.hsv_config['lv']]),
                np.array([st.session_state.hsv_config['uh'], st.session_state.hsv_config['us'], st.session_state.hsv_config['uv']])
            )
            mask = invert_mask(apply_morph(raw))
            if st.button("Save HSV Config", key=f"save_{idx}"):
                json.dump(st.session_state.hsv_config, open(CONFIG_FILE,'w'), indent=2)

        if choice and mask is not None:
            c1, c2, c3 = st.columns(3)
            c1.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
            c2.image(mask, caption="Mask", use_container_width=True)
            c3.image(extract(img, mask), caption="Objects", use_container_width=True)

            if st.button("Next", key=f"next_{idx}"):
                out = extract(img, mask)
                fname = f"{choice}_{idx}.png"
                cv2.imwrite(os.path.join(st.session_state.extract_dir, fname), out)
                # prepare for next
                st.session_state.choice = None
                st.session_state.idx += 1
                if hasattr(st, 'experimental_rerun'):
                    st.experimental_rerun()
                else:
                    st.stop()
    else:
        # All done: zip and cleanup
        zip_path = os.path.join(st.session_state.tmp, 'output.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(st.session_state.extract_dir):
                zf.write(os.path.join(st.session_state.extract_dir, f), f)
        shutil.rmtree(st.session_state.extract_dir)
        st.download_button("Download ZIP", data=open(zip_path,'rb'), file_name='extracted_objects.zip')
        st.success("Done!")

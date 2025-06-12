import os, json, re, random, shutil
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import pandas as pd
from tqdm import tqdm

# CONFIG
API_KEY = "AIzaSyBvs5d3T85nkd4qAcnLnC38owQ4hUVstPg"  
SOURCE_IMAGES = "input_images"
DATASET_DIR = "dataset"
SPLIT_RATIOS = {"train": 0.7, "val": 0.2, "test": 0.1}
CLASS_MAP = {"triangle": 0, "half circle": 1, "cube": 2, "rectangle": 3, "cylinder": 4, "arch": 5}

# Initialize Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Setup folders
for split in ["train", "val", "test"]:
    os.makedirs(os.path.join(DATASET_DIR, "images", split), exist_ok=True)
    os.makedirs(os.path.join(DATASET_DIR, "labels", split), exist_ok=True)
os.makedirs(os.path.join(DATASET_DIR, "visualize"), exist_ok=True)

# Prepare dataset split
all_files = [f for f in os.listdir(SOURCE_IMAGES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
random.shuffle(all_files)
N = len(all_files)
splits = {}
start = 0
for split, ratio in SPLIT_RATIOS.items():
    count = int(N * ratio)
    splits[split] = all_files[start:start+count]
    start += count

# Gemini prompt
prompt = """
You will receive one image (640x640) containing one or more geometric shapes:
triangle, half circle, cube, rectangle, cylinder, arch.
Return a pure JSON array of objects:
- label: shape name (string)
- box_2d: [ymin, xmin, ymax, xmax] (0-1000 scale).
NO markdown, NO explanation, only valid JSON.
"""

history = []

# Process each split
for split, files in splits.items():
    print(f"🔄 Processing {split} set ({len(files)} images)")
    for filename in tqdm(files):
        img_path = os.path.join(SOURCE_IMAGES, filename)
        img = Image.open(img_path).convert("RGB").resize((640, 640))

        try:
            resp = model.generate_content([img, prompt])
            text = resp.text.strip()
            match = re.search(r"\[.*\]", text, re.DOTALL)
            raw = match.group(0) if match else text
            objects = json.loads(raw)
        except Exception as e:
            print(f"❌ Error on {filename}: {e}")
            continue

        # Create YOLO label file
        w, h = 640, 640
        yolo_lines = []
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        for obj in objects:
            lbl = obj.get("label", "").lower()
            if lbl not in CLASS_MAP: continue
            ymin, xmin, ymax, xmax = obj["box_2d"][:4]

            # draw debug
            x1, y1 = xmin/1000*w, ymin/1000*h
            x2, y2 = xmax/1000*w, ymax/1000*h
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            draw.text((x1, y1-10), lbl, fill="red", font=font)

            xc = ((x1+x2)/2)/w
            yc = ((y1+y2)/2)/h
            bw = (x2-x1)/w
            bh = (y2-y1)/h
            yolo_lines.append(f"{CLASS_MAP[lbl]} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        # Save label
        label_fn = os.path.splitext(filename)[0] + ".txt"
        with open(os.path.join(DATASET_DIR, "labels", split, label_fn), "w") as f:
            f.write("\n".join(yolo_lines))

        # Save image
        shutil.copy(img_path, os.path.join(DATASET_DIR, "images", split, filename))

        # Save debug image (optional)
        img.save(os.path.join(DATASET_DIR, "visualize", f"{split}_{filename}"))

        # Log history
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": getattr(resp, "model_version", "gemini-2.0-flash"),
            "objects": objects,
            "source_image": filename
        }
        history.append(history_entry)

# Save history log
with open(os.path.join(DATASET_DIR, "history.json"), "w") as f:
    json.dump(history, f, indent=2)

print("✅ Dataset generation completed!")

import os, json, time, re
from PIL import Image, ImageDraw
import google.generativeai as genai

# CONFIGURATION
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

RAW_DIR = "raw_data"
PREPROCESS_DIR = "preprocessed"
LABELED_DIR = "labeled"
DEBUG_DIR = "debug_visuals"
HISTORY_FILE = "history.json"
RATE_LIMIT_SLEEP = 5  # safe for 15req/min

CLASSES = ["rectangle", "arch", "cube", "cylinder", "triangle", "half circle"]
CLASS_MAP = {label: i for i, label in enumerate(CLASSES)}

# Create folders
for d in [PREPROCESS_DIR, LABELED_DIR, DEBUG_DIR]:
    os.makedirs(d, exist_ok=True)

# STEP 1️⃣ — Resize images to 640x640 directly (NO PATCHING)
def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    resized_img = img.resize((640, 640))
    out_filename = os.path.basename(image_path).split('.')[0] + ".jpeg"
    resized_img.save(os.path.join(PREPROCESS_DIR, out_filename))

# STEP 2️⃣ — Full dataset preprocessing
for file in os.listdir(RAW_DIR):
    if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
        continue
    preprocess_image(os.path.join(RAW_DIR, file))
print("✅ All raw images resized into 640x640.")

# STEP 3️⃣ — Labeling loop
# Load history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE) as f:
        history = set(json.load(f))
else:
    history = set()

# Loop over resized images
patches = [f for f in os.listdir(PREPROCESS_DIR) if f.endswith(".jpeg")]
for patch_file in patches:
    if patch_file in history:
        continue

    patch_path = os.path.join(PREPROCESS_DIR, patch_file)
    patch_img = Image.open(patch_path).convert("RGB")

    prompt = """
The image contains one or more geometric shapes.
Possible labels: rectangle, arch, cube, cylinder, triangle, half circle.
Return a JSON list of objects.
Each object must contain:
- "label": string (choose only from allowed labels)
- "box_2d": [ymin, xmin, ymax, xmax] relative to image size 640x640.
NO markdown, ONLY valid JSON list.
"""

    try:
        resp = model.generate_content([patch_img, prompt])
        text = resp.text.strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        objects = json.loads(match.group(0))

        # Build YOLO label file
        yolo_lines = []
        draw = ImageDraw.Draw(patch_img)
        for obj in objects:
            label = obj["label"].lower()
            if label not in CLASS_MAP:
                continue
            y1, x1, y2, x2 = obj["box_2d"]
            xc = ((x1 + x2) / 2) / 640
            yc = ((y1 + y2) / 2) / 640
            bw = (x2 - x1) / 640
            bh = (y2 - y1) / 640
            yolo_lines.append(f"{CLASS_MAP[label]} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
            draw.rectangle([x1, y1, x2, y2], outline="yellow", width=2)
            draw.text((x1, y1-10), label, fill="yellow")

        # Save YOLO label
        label_filename = patch_file.replace(".jpeg", ".txt")
        with open(os.path.join(LABELED_DIR, label_filename), "w") as f:
            f.write("\n".join(yolo_lines))

        # Save debug image
        patch_img.save(os.path.join(DEBUG_DIR, patch_file))

        print(f"✅ Labeled: {patch_file}")

        # Update history
        history.add(patch_file)
        with open(HISTORY_FILE, "w") as f:
            json.dump(list(history), f, indent=2)

    except Exception as e:
        print(f"⚠ Error on {patch_file}: {str(e)}")

    time.sleep(RATE_LIMIT_SLEEP)

# lab/relabeler.py

import os, json, re
import google.generativeai as genai
from PIL import Image

API_KEY = os.environ['GEMINI_API_KEY']
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

DATASET_DIR = "dataset"
CLASSES = ["triangle", "half circle", "cube", "rectangle", "cylinder", "arch"]
CLASS_MAP = {name: i for i, name in enumerate(CLASSES)}

def relabel_one(split, filename):
    img_path = os.path.join(DATASET_DIR, "images", split, filename)
    img = Image.open(img_path).convert("RGB").resize((640, 640))

    prompt = """
    You will receive one image (640x640) containing one or more geometric shapes:
    triangle, half circle, cube, rectangle, cylinder, arch.
    Return a pure JSON array of objects:
    - label: shape name (string)
    - box_2d: [ymin, xmin, ymax, xmax] (0-1000 scale).
    NO markdown, NO explanation, only valid JSON.
    """

    resp = model.generate_content([img, prompt])
    text = resp.text.strip()
    m = re.search(r"\[.*\]", text, re.DOTALL)
    objects = json.loads(m.group(0))

    w, h = 640, 640
    yolo_lines = []
    for obj in objects:
        lbl = obj.get("label","").lower()
        if lbl not in CLASS_MAP: continue
        ymin, xmin, ymax, xmax = obj["box_2d"][:4]
        x1, y1 = xmin/1000*w, ymin/1000*h
        x2, y2 = xmax/1000*w, ymax/1000*h
        xc = ((x1+x2)/2)/w
        yc = ((y1+y2)/2)/h
        bw = (x2-x1)/w
        bh = (y2-y1)/h
        yolo_lines.append(f"{CLASS_MAP[lbl]} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

    # Overwrite
    label_path = os.path.join(DATASET_DIR, "labels", split, filename.replace(".jpeg", ".txt"))
    with open(label_path, "w") as f:
        f.write("\n".join(yolo_lines))
    print(f"✅ Updated: {label_path}")

# Example:
relabel_one("train", "somefile.jpeg")

import os, json, re
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# ——— CONFIGURAȚII ———
genai.configure(api_key="AIzaSyBGrFAcH43_M8xayzWUMgBHbCDx61e4T2E")
model = genai.GenerativeModel(model_name="gemini-2.0-flash")
IMAGE_PATH = "image1.jpeg"
OUTPUT_IMG = "debug_shapes.jpg"
YOLO_LABEL = "shapes.txt"
CLASS_MAP = {"triangle":0, "half circle":1, "cube":2, "rectangle":3, "cylinder":4, "arch":5}
IMG_DIR = "images"
LBL_DIR = "labels"

# Asigură structura YOLO
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(LBL_DIR, exist_ok=True)
# Copie imagine originală în images/
Image.open(IMAGE_PATH).save(os.path.join(IMG_DIR, IMAGE_PATH))

# ——— Apel Gemini ———
prompt = """
I will show you an image (640×640) of geometric shapes:
triangle, half circle, cube, rectangle, cylinder, arch.
Return ONLY a pure JSON array of objects. Each object MUST contain EXACTLY:
  - label: the shape name (string)
  - box_2d: array of exactly 4 numbers [ymin, xmin, ymax, xmax] (0–1000 scale).
NO markdown, no extra fields, no explanations.
"""
img = Image.open(IMAGE_PATH).convert("RGB").resize((640,640))
resp = model.generate_content([img, prompt])
text = resp.text.strip()
m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
raw = m.group(1) if m else text
objects = json.loads(raw)

# ——— Desen, YOLO & Label ———
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
h, w = img.size[1], img.size[0]
yolo_lines = []

for obj in objects:
    lbl = obj.get("label","").lower()
    if lbl not in CLASS_MAP: continue
    ymin, xmin, ymax, xmax = obj["box_2d"][:4]  # ia doar primele 4 valori

    # Convertire pixeli
    x1, y1 = xmin/1000*w, ymin/1000*h
    x2, y2 = xmax/1000*w, ymax/1000*h

    # Desenează
    draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
    draw.text((x1, y1-10), lbl, fill="red", font=font)

    # Normalizează YOLO cx, cy, w, h :contentReference[oaicite:6]{index=6}
    xc = ((x1+x2)/2)/w
    yc = ((y1+y2)/2)/h
    bw = (x2-x1)/w
    bh = (y2-y1)/h
    yolo_lines.append(f"{CLASS_MAP[lbl]} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

# ——— Salvează imagine + label în folders specifice YOLO ———
img.save(os.path.join(IMG_DIR, IMAGE_PATH))
label_fn = os.path.splitext(IMAGE_PATH)[0] + ".txt"
with open(os.path.join(LBL_DIR, label_fn), "w") as f:
    f.write("\n".join(yolo_lines))
print(f"✅ Salvate în `{IMG_DIR}/` și `{LBL_DIR}/`")

# ——— Istoric folosind timestamp corect și versiune model ———
history = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "model_version": getattr(resp, "model_version", "gemini-2.0-flash"),
    "usage": {
        "prompt_tokens": resp.usage_metadata.prompt_token_count,
        "candidates_tokens": resp.usage_metadata.candidates_token_count,
        "total_tokens": resp.usage_metadata.total_token_count
    },
    "objects": objects
}
with open("history.json", "a+") as f:
    f.seek(0, os.SEEK_END)
    if f.tell()==0:
        json.dump([history], f, indent=2)
    else:
        f.seek(0)
        data = json.load(f)
        data.append(history)
        f.seek(0)
        json.dump(data, f, indent=2)
print("✅ Istoricul actualizat în history.json")

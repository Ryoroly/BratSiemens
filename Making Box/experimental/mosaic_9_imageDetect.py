import os, re, json
from PIL import Image, ImageDraw
import google.generativeai as genai

# CONFIG
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Create mosaic
imgs = [Image.open(f"mosaic/{i}.jpeg").convert("RGB").resize((640, 640)) for i in range(1, 10)]
grid = Image.new('RGB', (640 * 3, 640 * 3))
for idx, img in enumerate(imgs):
    x, y = (idx % 3) * 640, (idx // 3) * 640
    grid.paste(img, (x, y))
grid.save("mosaic_combined.jpeg")

# Gemini prompt — no mention of mosaic!
prompt = """
Return a JSON list of objects.
Each object must contain:
- "label": string
- "box_2d": array [ymin, xmin, ymax, xmax]
Use pixel coordinates matching the image size. Only JSON.
"""

resp = model.generate_content([grid, prompt])
text = resp.text.strip()
print(resp)
match = re.search(r"\[.*\]", text, re.DOTALL)
raw_json = match.group(0)
objects = json.loads(raw_json)

# Parse robustly
parsed_objects = []
for obj in objects:
    label = obj["label"]
    y1, x1, y2, x2 = obj["box_2d"]
    parsed_objects.append({"label": label, "box_2d": [y1, x1, y2, x2]})

# Draw boxes on full mosaic for debug
draw = ImageDraw.Draw(grid)
for obj in parsed_objects:
    y1, x1, y2, x2 = obj["box_2d"]
    draw.rectangle([x1, y1, x2, y2], outline="yellow", width=4)
    draw.text((x1, y1 - 15), obj["label"], fill="yellow")
grid.save("mosaic_annotated.jpeg")

# Split boxes into sub-images based on box center
subs = {i: [] for i in range(9)}
for obj in parsed_objects:
    y1, x1, y2, x2 = obj["box_2d"]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    col = int(cx // 640)
    row = int(cy // 640)
    idx = row * 3 + col
    off_x, off_y = col * 640, row * 640
    obj_local = {
        "label": obj["label"],
        "box_2d": [
            y1 - off_y,
            x1 - off_x,
            y2 - off_y,
            x2 - off_x
        ]
    }
    subs[idx].append(obj_local)

# Export split images + boxes
for i, objs in subs.items():
    print(f"Image {i+1}: {len(objs)} detections")
    sub_img = imgs[i].copy()
    sd = ImageDraw.Draw(sub_img)
    for o in objs:
        y1, x1, y2, x2 = o["box_2d"]
        sd.rectangle([x1, y1, x2, y2], outline="red", width=3)
        sd.text((x1, y1 - 10), o["label"], fill="red")
    sub_img.save(f"split_{i+1}_annotated.jpeg")

import os, re, json
from PIL import Image, ImageDraw
import google.generativeai as genai

# CONFIG
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Mosaic parameters
GRID_ROWS = 1
GRID_COLS = 2
CELL_SIZE = 640  # each image size

# STEP 1️⃣ Load images from mosaic folder and resize individually first
imgs = [Image.open(f"mosaic/{i}.jpeg").convert("RGB").resize((CELL_SIZE, CELL_SIZE)) for i in range(4, 6+1)]

# STEP 2️⃣ Build mosaic image dynamically
mosaic_width = GRID_COLS * CELL_SIZE  # 1280
mosaic_height = GRID_ROWS * CELL_SIZE # 1280
grid = Image.new('RGB', (mosaic_width, mosaic_height))
for idx, img in enumerate(imgs):
    x = (idx % GRID_COLS) * CELL_SIZE
    y = (idx // GRID_COLS) * CELL_SIZE
    grid.paste(img, (x, y))
grid.save("mosaic_combined.jpeg")

# STEP 3️⃣ Gemini prompt — image size is now 1280x1280
prompt = """
You will analyze this image (size 1280x640).

Make sure you understand this image size.

1. First, detect all visible shapes.
2. For each detected object, classify it into one of: rectangle, arch, cube, cylinder, triangle, half circle.
3. Make sure the box is EXACTLY on the detected object
4. Return a strict JSON array of:
  {"label": string, "box_2d": [ymin, xmin, ymax, xmax]} (in pixel coordinates)
No extra text. No markdown.

"""

# STEP 4️⃣ Gemini call
resp = model.generate_content([grid, prompt])
text = resp.text.strip()
print(resp)
match = re.search(r"\[.*\]", text, re.DOTALL)
raw_json = match.group(0)
objects = json.loads(raw_json)

# STEP 5️⃣ Parse Gemini output directly
parsed_objects = []
for obj in objects:
    label = obj["label"]
    y1, x1, y2, x2 = obj["box_2d"]
    parsed_objects.append({"label": label, "box_2d": [y1, x1, y2, x2]})

# STEP 6️⃣ Draw all detections on full mosaic for debug
draw = ImageDraw.Draw(grid)
for obj in parsed_objects:
    y1, x1, y2, x2 = obj["box_2d"]
    draw.rectangle([x1, y1, x2, y2], outline="yellow", width=4)
    draw.text((x1, y1 - 15), obj["label"], fill="yellow")
grid.save("mosaic_debug_boxes.jpeg")

# STEP 7️⃣ Split into sub-images based on center coordinates
subs = {i: [] for i in range(GRID_ROWS * GRID_COLS)}
for obj in parsed_objects:
    y1, x1, y2, x2 = obj["box_2d"]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    col = int(cx // CELL_SIZE)
    row = int(cy // CELL_SIZE)
    idx = row * GRID_COLS + col
    off_x, off_y = col * CELL_SIZE, row * CELL_SIZE
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

# STEP 8️⃣ Export split images + boxes
for i in range(GRID_ROWS * GRID_COLS):
    sub_img = imgs[i].copy()
    draw_sub = ImageDraw.Draw(sub_img)
    for o in subs[i]:
        y1, x1, y2, x2 = o["box_2d"]
        draw_sub.rectangle([x1, y1, x2, y2], outline="red", width=3)
        draw_sub.text((x1, y1 - 10), o["label"], fill="red")
    sub_img.save(f"split_{i+1}_annotated.jpeg")
    print(f"Image {i+1}: {len(subs[i])} detections")

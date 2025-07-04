# server_api.py
from flask import Flask, request, jsonify
import asyncio
from bleak import BleakClient, BleakScanner
import cv2
import base64
import numpy as np

app = Flask(__name__)

# BLE configuration
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
CHAR_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
ARDUINO_MAC = "F4:12:FA:6F:91:21"

# Class mapping
CLASS_ID = {
    'cube': 1,
    'cylinder': 2,
    'half_circle': 3,
    'arch': 4,
    'triangle': 5,
    'rectangle': 6
}

# Global storage
latest_data = {"image": None, "detections": [], "raw_image": None}
is_ready = True  # Flag to control when RPi can send data

def resize_image_for_display(img_b64, max_width=640):
    """Resize image while maintaining aspect ratio for display"""
    if not img_b64:
        return None
    
    img_data = base64.b64decode(img_b64)
    img_array = np.frombuffer(img_data, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    if img is None:
        return None
    
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

async def send_ble(payload):
    """Send BLE commands to Arduino"""
    try:
        device = await BleakScanner.find_device_by_address(ARDUINO_MAC, timeout=10.0)
        if not device:
            print("❌ Arduino BLE not found.")
            return False
        
        async with BleakClient(device) as client:
            print(f"✔ Connected to {device.address}")
            
            # Send crop shape
            w, h = payload['crop_shape']
            s_msg = f"S {w} {h}"
            await client.write_gatt_char(CHAR_UUID, s_msg.encode())
            print(f"▶ Sent BLE: {s_msg}")
            
            # Send highest-confidence detection
            dets = payload.get('detections', [])
            if dets:
                best = max(dets, key=lambda d: d['confidence'])
                cx, cy = map(int, best['center_px'])
                obj_id = CLASS_ID.get(best['class'], 1)
                t_msg = f"T {cx} {cy} {obj_id}"
                await client.write_gatt_char(CHAR_UUID, t_msg.encode())
                print(f"▶ Sent BLE: {t_msg}")
                return True
            else:
                print("⚠ No detections to send.")
                return False
    except Exception as e:
        print(f"❌ BLE Error: {e}")
        return False

@app.route("/ready", methods=["GET"])
def ready_check():
    """RPi polls this to know when to send data"""
    return jsonify({"ready": is_ready})

@app.route("/data", methods=["POST"])
def receive_data():
    """Original endpoint from server_with_ble.py"""
    global latest_data, is_ready
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    
    data = request.get_json()
    print(f"📥 Received: {len(data.get('detections', []))} detections")
    
    # Store data for Streamlit
    latest_data["detections"] = data.get("detections", [])
    latest_data["crop_shape"] = data.get("crop_shape", [])
    
    # Set not ready during processing
    is_ready = False
    
    # Try to send BLE if detections exist
    if latest_data["detections"]:
        try:
            success = asyncio.run(send_ble(data))
            if success:
                print("✅ BLE command sent successfully")
            else:
                print("⚠ BLE command failed")
        except Exception as e:
            print(f"❌ BLE async error: {e}")
    else:
        print("⚠ No detections to send")
    
    # Ready for next request
    is_ready = True
    
    return jsonify({'status': 'success', 'received_count': len(data.get('detections', []))}), 200

@app.route("/post", methods=["POST"])
def post_data():
    """Keep original endpoint for image data"""
    global latest_data
    data = request.get_json()
    
    # Store original image and detections
    latest_data["image"] = data.get("image")
    latest_data["detections"] = data.get("detections", [])
    
    # Create resized version for display
    latest_data["raw_image"] = resize_image_for_display(data.get("image"))
    
    print("✅ Received POST:", len(latest_data.get("detections", [])), "detections")
    
    return jsonify({"status": "ok"})

@app.route("/get", methods=["GET"])
def get_data():
    return jsonify(latest_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
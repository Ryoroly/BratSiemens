# app_getImage.py
import streamlit as st
from threading import Thread
import requests
import base64
import numpy as np
import cv2
import time
import server_api

# Function to run the Flask server in a background thread
def run_flask():
    server_api.app.run(host="0.0.0.0", port=5010)

# Start Flask in the background if not already started
if 'flask_started' not in st.session_state:
    thread = Thread(target=run_flask, daemon=True)
    thread.start()
    st.session_state.flask_started = True

st.title("💻 Streamlit App with Flask Server & BLE")

# Function to decode base64 image
def decode_image(img_b64):
    if not img_b64:
        return None
    img_data = base64.b64decode(img_b64)
    img_array = np.frombuffer(img_data, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Function to fetch and display the image with detections
def fetch_and_display():
    try:
        response = requests.get("http://localhost:5010/get", timeout=3)
        response.raise_for_status()
        data = response.json()
        
        detections = data.get("detections", [])
        
        # If we have detections, show processed image with annotations
        if detections:
            img_b64 = data.get("image")
            if img_b64:
                img = decode_image(img_b64)
                if img is not None:
                    # Draw detections
                    for det in detections:
                        if 'center_px' in det:
                            x, y = map(int, det['center_px'])
                            y = img.shape[0] - y
                            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
                            label = f"{det.get('class', '')} ({det.get('confidence', 0):.2f})"
                            cv2.putText(img, label, (x + 10, y),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    return img, f"Detections: {len(detections)}"
        
        # If no detections, show raw image (lower resolution)
        else:
            raw_img_b64 = data.get("raw_image")
            if raw_img_b64:
                img = decode_image(raw_img_b64)
                if img is not None:
                    return img, "No detections - showing raw image"
        
        return None, "No image data available"
    
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, f"Error: {e}"

# Create placeholders
image_placeholder = st.empty()
status_placeholder = st.empty()

# Auto-refresh loop
while True:
    img, status = fetch_and_display()
    
    if img is not None:
        image_placeholder.image(img, caption="Latest Image", use_container_width=True)
    
    status_placeholder.text(status)
    time.sleep(0.1)  # Adjust the sleep time as needed
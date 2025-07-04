"""Module for sending detection data to Flask server."""

import requests
import base64
import time
from io import BytesIO
from PIL import Image
import numpy as np

from config import FLASK_PORT


class DetectionSender:
    def __init__(self):
        self.flask_url = f"http://localhost:{FLASK_PORT}"
    
    def prepare_payload(self, detections, image_array, timestamp=None):
        """Prepare detection payload with all required fields."""
        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Convert image to base64
        if image_array is not None:
            # Get image dimensions for crop_shape
            if len(image_array.shape) == 3:
                h, w, _ = image_array.shape
            else:
                h, w = image_array.shape
            
            # Convert to PIL Image and then to base64
            if image_array.dtype != np.uint8:
                image_array = (image_array * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image_array)
            buffer = BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
        else:
            # Default dimensions if no image
            w, h = 640, 480
            image_base64 = None
        
        # Prepare payload with MANDATORY crop_shape
        payload = {
            'detections': detections,
            'crop_shape': [w, h],  # OBLIGATORIU!
            'timestamp': timestamp
        }
        
        # Add image only if available
        if image_base64:
            payload['image'] = image_base64
        
        return payload
    
    def send_detection(self, detections, image_array=None, timestamp=None):
        """Send detection data to Flask server."""
        try:
            payload = self.prepare_payload(detections, image_array, timestamp)
            
            # Validate payload
            if 'crop_shape' not in payload:
                raise ValueError("crop_shape is mandatory!")
            
            print(f"📤 Sending {len(detections)} detections with crop_shape {payload['crop_shape']}")
            
            response = requests.post(
                f"{self.flask_url}/data",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                print(f"✅ Detection sent! BLE Status: {status}")
                return True
            else:
                print(f"❌ Send failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

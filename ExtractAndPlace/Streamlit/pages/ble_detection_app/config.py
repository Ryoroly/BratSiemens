"""Configuration settings for the BLE detection application."""

# BLE Configuration
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
CHAR_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
ARDUINO_MAC = "F4:12:FA:6F:91:21"

# Class mapping for object detection
CLASS_ID = {
    'cube': 1,
    'cylinder': 2,
    'half_circle': 3,
    'arch': 4,
    'triangle': 5,
    'rectangle': 6
}

# Server configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5003
STREAMLIT_PORT = 8501

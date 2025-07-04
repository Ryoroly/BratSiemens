"""Configuration settings for the BLE detection application."""

# BLE Configuration
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
CHAR_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"  # pentru date S/T
CHAR_UUID_STATUS = "19B10002-E8F2-537E-4F6C-D104768A1214"  # pentru notificări 0/1
ARDUINO_MAC = "F4:12:FA:6F:91:21"

# Class mapping for object detection (updated to match your working script)
CLASS_ID = {
    'triangle': 1,
    'rectangle': 2,
    'arch': 3,
    'cube': 4,
}

# Server configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5003          # Port pentru Flask server (API)
STREAMLIT_PORT = 8501      # Port pentru Streamlit UI

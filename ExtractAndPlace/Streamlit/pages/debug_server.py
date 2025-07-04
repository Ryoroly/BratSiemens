"""Debug script to test Flask server startup."""

import sys
import os

# Add the ble_detection_app folder to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
ble_app_dir = os.path.join(current_dir, 'ble_detection_app')
sys.path.insert(0, ble_app_dir)

print(f"📁 Current dir: {current_dir}")
print(f"📁 BLE app dir: {ble_app_dir}")
print(f"📁 BLE app exists: {os.path.exists(ble_app_dir)}")

# List files in ble_detection_app
if os.path.exists(ble_app_dir):
    files = os.listdir(ble_app_dir)
    print(f"📁 Files in ble_detection_app: {files}")

try:
    print("🔄 Importing config...")
    from ble_detection_app.config import FLASK_HOST, FLASK_PORT
    print(f"✅ Config imported - Host: {FLASK_HOST}, Port: {FLASK_PORT}")
    
    print("🔄 Importing flask_server...")
    from ble_detection_app.flask_server import flask_server
    print("✅ Flask server imported")
    
    print("🔄 Testing Flask app...")
    app = flask_server.app
    print(f"✅ Flask app created: {app}")
    
    print("🔄 Starting Flask server...")
    flask_server.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

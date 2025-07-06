"""Main entry point for the BLE detection application."""

import sys
import os
import subprocess
import threading
import time
import argparse
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 


# Add the ble_detection_app folder to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
ble_app_dir = os.path.join(current_dir, 'ble_detection_app')
sys.path.insert(0, ble_app_dir)

# Now we can import from the ble_detection_app folder
from ble_detection_app.flask_server import flask_server
from ble_detection_app.config import FLASK_HOST, FLASK_PORT


def run_flask_server():
    """Run the Flask server."""
    print(f"🚀 Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    try:
        flask_server.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")


def run_streamlit_ui(test_mode=False):
    """Run the Streamlit UI."""
    if test_mode:
        print("🧪 Starting Streamlit Test & Debug UI...")
        ui_file = "streamlit_test_ui.py"
        port = "8502"  # Different port for test mode
    else:
        print("🚀 Starting Streamlit UI...")
        ui_file = "streamlit_ui.py"
        port = "8501"
    
    print(f"📡 Will connect to Flask server at localhost:{FLASK_PORT}")
    
    # Change to the ble_detection_app directory to run streamlit
    original_dir = os.getcwd()
    try:
        os.chdir(ble_app_dir)
        subprocess.run([sys.executable, "-m", "streamlit", "run", ui_file, "--server.port", port])
    finally:
        os.chdir(original_dir)


def run_both(test_mode=False):
    """Run both server and UI."""
    if test_mode:
        print("🧪 Starting Flask server and Streamlit Test & Debug UI...")
        print(f"📡 Flask server will run on port {FLASK_PORT}")
        print("📡 Streamlit Test UI will run on port 8502")
    else:
        print("🚀 Starting both Flask server and Streamlit UI...")
        print(f"📡 Flask server will run on port {FLASK_PORT}")
        print("📡 Streamlit UI will run on port 8501")
    
    # Start Flask server in background thread
    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    print("⏳ Waiting for Flask server to start...")
    time.sleep(3)
    
    # Start Streamlit UI (this will block)
    run_streamlit_ui(test_mode)


def test_connection():
    """Test if we can connect to the Flask server."""
    import requests
    try:
        response = requests.get(f"http://localhost:{FLASK_PORT}/status", timeout=5)
        print(f"✅ Flask server is running on port {FLASK_PORT}")
        return True
    except:
        print(f"❌ Cannot connect to Flask server on port {FLASK_PORT}")
        return False


def main():
    parser = argparse.ArgumentParser(description="BLE Detection Application")
    parser.add_argument("--mode", choices=["server", "ui", "both", "test"], default="both",
                       help="Run mode: server only, ui only, both, or test connection")
    parser.add_argument("--test", action="store_true", 
                       help="Enable test mode with full debugging and logging features")
    
    args = parser.parse_args()
    
    print(f"📁 Working from: {current_dir}")
    print(f"📁 BLE App folder: {ble_app_dir}")
    print(f"🔧 Flask server will use port: {FLASK_PORT}")
    
    if args.test:
        print("🧪 TEST MODE ENABLED - Full debugging and logging features active")
    
    if not os.path.exists(ble_app_dir):
        print(f"❌ Error: ble_detection_app folder not found at {ble_app_dir}")
        return
    
    if args.mode == "server":
        run_flask_server()
    elif args.mode == "ui":
        run_streamlit_ui(args.test)
    elif args.mode == "test":
        test_connection()
    else:
        run_both(args.test)


if __name__ == "__main__":
    main()

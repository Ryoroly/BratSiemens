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


def run_streamlit_ui():
    """Run the Streamlit UI."""
    print("🚀 Starting Streamlit UI...")
    print(f"📡 Will connect to Flask server at localhost:{FLASK_PORT}")
    
    # Change to the ble_detection_app directory to run streamlit
    original_dir = os.getcwd()
    try:
        os.chdir(ble_app_dir)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_ui.py", "--server.port", "8501"])
    finally:
        os.chdir(original_dir)


def run_both():
    """Run both server and UI."""
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
    run_streamlit_ui()


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
    
    args = parser.parse_args()
    
    print(f"📁 Working from: {current_dir}")
    print(f"📁 BLE App folder: {ble_app_dir}")
    print(f"🔧 Flask server will use port: {FLASK_PORT}")
    
    if not os.path.exists(ble_app_dir):
        print(f"❌ Error: ble_detection_app folder not found at {ble_app_dir}")
        return
    
    if args.mode == "server":
        run_flask_server()
    elif args.mode == "ui":
        run_streamlit_ui()
    elif args.mode == "test":
        test_connection()
    else:
        run_both()


if __name__ == "__main__":
    main()

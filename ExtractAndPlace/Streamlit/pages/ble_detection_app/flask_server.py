"""Flask server for receiving detection data and serving to Streamlit."""

from flask import Flask, request, jsonify
import asyncio
import sys
import os
import threading

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from ble_handler import BLEHandler
    print("✅ BLEHandler imported successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not import BLEHandler: {e}")
    BLEHandler = None

try:
    from data_storage import data_store
    print("✅ data_store imported successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not import data_store: {e}")
    data_store = None

try:
    from config import FLASK_HOST, FLASK_PORT
    print(f"✅ Config imported - Host: {FLASK_HOST}, Port: {FLASK_PORT}")
except Exception as e:
    print(f"⚠️ Warning: Could not import config: {e}")
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5001


class FlaskServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.ble_handler = BLEHandler() if BLEHandler else None
        self._setup_routes()
        print("✅ FlaskServer initialized")

    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/data', methods=['POST'])
        def receive_data():
            try:
                if not request.is_json:
                    return jsonify({'error': 'Content-Type must be application/json'}), 415

                payload = request.get_json()
                #print(f"📥 Received: {payload}")
                
                # Store data for Streamlit
                if data_store:
                    data_store.store_data(payload)
                
                # Send over BLE using the new logic
                if self.ble_handler:
                    status = asyncio.run(self.ble_handler.send_data(payload))
                    print(f"📡 BLE Status: {status}")
                else:
                    print("⚠️ BLE handler not available")
                    status = 'no_ble'
                
                return jsonify({
                    'status': status, 
                    'received_count': len(payload.get('detections', []))
                }), 200
            except Exception as e:
                #print(f"❌ Error in receive_data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/ready', methods=['GET'])
        def check_ready():
            """Endpoint pentru a verifica dacă brațul este gata de următoarea comandă."""
            try:
                if self.ble_handler:
                    ready = self.ble_handler.is_ready()
                    return jsonify({'ready': ready}), 200
                else:
                    return jsonify({'ready': False, 'error': 'BLE handler not available'}), 200
            except Exception as e:
                print(f"❌ Error in check_ready: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/get', methods=['GET'])
        def get_data():
            """Endpoint for Streamlit to fetch latest data."""
            try:
                if data_store:
                    latest_data = data_store.get_latest_data()
                else:
                    latest_data = {'detections': [], 'message': 'No data store available'}
                return jsonify(latest_data)
            except Exception as e:
                print(f"❌ Error in get_data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get server status."""
            try:
                if data_store:
                    detection_count = data_store.get_detection_count()
                    timestamp = data_store.get_latest_data().get('timestamp', 0)
                else:
                    detection_count = 0
                    timestamp = 0
                
                ble_status = {}
                if self.ble_handler:
                    ble_status = self.ble_handler.get_status()
                    
                return jsonify({
                    'status': 'running',
                    'detection_count': detection_count,
                    'timestamp': timestamp,
                    'ble_available': self.ble_handler is not None,
                    'ble_status': ble_status,
                    'data_store_available': data_store is not None
                })
            except Exception as e:
                print(f"❌ Error in get_status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/clear', methods=['POST'])
        def clear_data():
            """Clear stored data."""
            try:
                if data_store:
                    data_store.clear_data()
                    return jsonify({'status': 'cleared'})
                else:
                    return jsonify({'status': 'no data store available'})
            except Exception as e:
                print(f"❌ Error in clear_data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/test', methods=['GET'])
        def test_endpoint():
            """Test endpoint to verify server is working."""
            return jsonify({
                'status': 'Server is running!',
                'message': 'Flask server is working correctly',
                'ble_available': self.ble_handler is not None
            })

        print("✅ Flask routes setup complete")

    def run(self, host=None, port=None, debug=False):
        """Run the Flask server."""
        host = host or FLASK_HOST
        port = port or FLASK_PORT
        
        print(f"🚀 Starting Flask server on {host}:{port}")
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        except Exception as e:
            print(f"❌ Error starting Flask server: {e}")
            raise


# Create server instance
print("🔄 Creating FlaskServer instance...")
flask_server = FlaskServer()
app = flask_server.app  # For compatibility
print("✅ FlaskServer instance created")

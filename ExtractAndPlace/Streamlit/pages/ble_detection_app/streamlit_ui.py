"""Streamlit UI for visualizing detection results."""

import streamlit as st
import requests
import time
from threading import Thread
import sys
import os

# Ensure we can import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from image_utils import ImageProcessor
from config import FLASK_PORT


class StreamlitUI:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.flask_url = f"http://localhost:{FLASK_PORT}"
        self.server_running = False

    def check_server_status(self):
        """Check if Flask server is running."""
        try:
            response = requests.get(f"{self.flask_url}/status", timeout=2)
            return response.status_code == 200
        except:
            return False

    def setup_page(self):
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title="BLE Detection Monitor",
            page_icon="🔍",
            layout="wide"
        )
        
        st.title("🔍 BLE Detection Monitor")
        st.markdown("Real-time object detection with BLE communication")
        st.markdown(f"**Connecting to Flask server:** `{self.flask_url}`")

    def check_flask_server(self):
        """Check Flask server status and update UI."""
        if self.check_server_status():
            self.server_running = True
            st.success(f"✅ Connected to Flask server at {self.flask_url}")
        else:
            self.server_running = False
            st.error(f"❌ Cannot connect to Flask server at {self.flask_url}")
            st.info("💡 Make sure the Flask server is running on port 5001")

    def fetch_detection_data(self):
        """Fetch latest detection data from Flask server."""
        if not self.server_running:
            return {}
            
        try:
            response = requests.get(f"{self.flask_url}/get", timeout=3)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.warning("🔄 Connection lost to Flask server")
            self.server_running = False
            return {}
        except requests.exceptions.Timeout:
            st.warning("⏱️ Request timeout")
            return {}
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            return {}

    def display_server_status(self):
        """Display server status in sidebar."""
        with st.sidebar:
            st.header("🖥️ Server Status")
            
            # Check server status
            if st.button("🔄 Check Server"):
                self.check_flask_server()
            
            if self.server_running:
                st.success("✅ Flask Server Online")
                try:
                    response = requests.get(f"{self.flask_url}/status", timeout=2)
                    status_data = response.json()
                    
                    # Basic server info
                    st.write(f"**Detection Count:** {status_data.get('detection_count', 0)}")
                    timestamp = status_data.get('timestamp', 0)
                    if timestamp:
                        st.write(f"**Last Update:** {time.ctime(timestamp)}")
                    
                    # BLE Status
                    st.subheader("📡 BLE Status")
                    ble_available = status_data.get('ble_available', False)
                    if ble_available:
                        st.success("✅ BLE Handler Available")
                        ble_status = status_data.get('ble_status', {})
                        
                        # BLE connection status
                        connected = ble_status.get('connected', False)
                        if connected:
                            st.success("🔗 BLE Connected")
                        else:
                            st.warning("⚠️ BLE Disconnected")
                        
                        # Arm status
                        arm_idle = ble_status.get('arm_idle', False)
                        if arm_idle:
                            st.success("🤖 Arm Ready")
                        else:
                            st.warning("🤖 Arm Busy")
                        
                        # Queue status
                        has_queued = ble_status.get('has_queued_payload', False)
                        if has_queued:
                            st.info("📋 Command Queued")
                        else:
                            st.info("📋 No Queued Commands")
                            
                    else:
                        st.error("❌ BLE Handler Not Available")
                    
                    # Check arm ready status
                    try:
                        ready_response = requests.get(f"{self.flask_url}/ready", timeout=2)
                        ready_data = ready_response.json()
                        arm_ready = ready_data.get('ready', False)
                        if arm_ready:
                            st.success("🎯 Ready for Commands")
                        else:
                            st.warning("⏳ Processing Command")
                    except:
                        pass
                        
                except Exception as e:
                    st.error(f"Error getting status: {e}")
            else:
                st.error("❌ Flask Server Offline")
                st.markdown(f"**Expected URL:** {self.flask_url}")
                st.markdown("**Troubleshooting:**")
                st.markdown("1. Check if Flask server is running")
                st.markdown("2. Verify port 5001 is not blocked")
                st.markdown("3. Try restarting the Flask server")

    def display_detection_info(self, data):
        """Display detection information in sidebar."""
        with st.sidebar:
            st.header("📊 Detection Info")
            
            detections = data.get("detections", [])
            st.metric("Detections Count", len(detections))
            
            if detections:
                st.subheader("🎯 Detected Objects")
                for i, det in enumerate(detections):
                    with st.expander(f"Object {i+1}: {det.get('class', 'Unknown')}"):
                        st.write(f"**Confidence:** {det.get('confidence', 0):.3f}")
                        if 'center_px' in det:
                            cx, cy = det['center_px']
                            st.write(f"**Position:** ({cx:.0f}, {cy:.0f})")
                        
                        # Show class mapping
                        class_name = det.get('class', 'Unknown')
                        from config import CLASS_ID
                        class_id = CLASS_ID.get(class_name, 'Unknown')
                        st.write(f"**Class ID:** {class_id}")
            
            # Crop shape info
            if 'crop_shape' in data:
                w, h = data['crop_shape']
                st.metric("Crop Size", f"{w}×{h}")

    def display_controls(self):
        """Display control panel."""
        st.header("🎛️ Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            auto_refresh = st.checkbox("Auto Refresh", value=False)
        
        with col2:
            refresh_rate = st.slider("Refresh Rate (s)", 0.5, 5.0, 1.0)
        
        with col3:
            if st.button("🗑️ Clear Data"):
                if self.server_running:
                    try:
                        requests.post(f"{self.flask_url}/clear", timeout=3)
                        st.success("✅ Data cleared!")
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("❌ Failed to clear data")
                else:
                    st.error("❌ Server not connected")
        
        with col4:
            if st.button("🔄 Refresh Now"):
                st.rerun()
        
        return auto_refresh, refresh_rate

    def test_connection(self):
        """Test connection to Flask server."""
        st.header("🔧 Connection Test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Flask Connection"):
                with st.spinner("Testing connection..."):
                    try:
                        response = requests.get(f"{self.flask_url}/test", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ Flask server is reachable!")
                            st.json(response.json())
                            self.server_running = True
                        else:
                            st.error(f"❌ Server returned status code: {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Connection refused - Flask server is not running")
                    except requests.exceptions.Timeout:
                        st.error("❌ Connection timeout")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        with col2:
            if st.button("Test BLE Ready"):
                if self.server_running:
                    with st.spinner("Checking BLE status..."):
                        try:
                            response = requests.get(f"{self.flask_url}/ready", timeout=5)
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('ready', False):
                                    st.success("✅ BLE Arm is ready!")
                                else:
                                    st.warning("⏳ BLE Arm is busy")
                                st.json(data)
                            else:
                                st.error(f"❌ Error: {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Server not connected")

    def send_test_data(self):
        """Send test detection data to server."""
        st.header("🧪 Test Data")
        
        if st.button("Send Test Detection"):
            if self.server_running:
                test_data = {
                    "detections": [
                        {
                            "class": "cube",
                            "confidence": 0.95,
                            "center_px": [320, 240]
                        }
                    ],
                    "crop_shape": [640, 480],
                    "timestamp": time.time()
                }
                
                try:
                    response = requests.post(
                        f"{self.flask_url}/data", 
                        json=test_data, 
                        timeout=5
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Test data sent! Status: {result.get('status')}")
                        st.json(result)
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error sending test data: {e}")
            else:
                st.error("❌ Server not connected")

    def run(self):
        """Run the Streamlit application."""
        self.setup_page()
        
        # Initial server check
        self.check_flask_server()
        
        # Connection test section
        self.test_connection()
        
        # Test data section
        self.send_test_data()
        
        # Server status in sidebar
        self.display_server_status()
        
        # Control panel
        auto_refresh, refresh_rate = self.display_controls()
        
        # Main content area
        st.header("📷 Detection Display")
        image_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Manual refresh or auto-refresh
        if auto_refresh and self.server_running:
            st.info("🔄 Auto-refresh enabled")
            
            # Create a placeholder for refresh counter
            refresh_counter = st.empty()
            
            # Auto-refresh loop
            for i in range(100):  # Limit to prevent infinite loop
                data = self.fetch_detection_data()
                
                if data:
                    # Display image
                    img, status = self.image_processor.process_detection_data(data)
                    if img is not None:
                        image_placeholder.image(
                            img, 
                            caption="Latest Detection", 
                            use_container_width=True
                        )
                    else:
                        image_placeholder.info("📷 Waiting for image data...")
                    
                    status_placeholder.info(f"📊 Status: {status}")
                    
                    # Display detection info in sidebar
                    self.display_detection_info(data)
                else:
                    status_placeholder.warning("⏳ Waiting for detection data...")
                
                # Show refresh counter
                refresh_counter.text(f"🔄 Refresh #{i+1} - Next in {refresh_rate}s")
                
                time.sleep(refresh_rate)
        else:
            # Manual refresh mode
            if self.server_running:
                data = self.fetch_detection_data()
                if data:
                    img, status = self.image_processor.process_detection_data(data)
                    if img is not None:
                        image_placeholder.image(
                            img, 
                            caption="Latest Detection", 
                            use_container_width=True
                        )
                    else:
                        image_placeholder.info("📷 No image data available")
                    
                    status_placeholder.info(f"📊 Status: {status}")
                    self.display_detection_info(data)
                else:
                    status_placeholder.info("📷 No detection data available")
                    st.info("💡 Send some detection data to the Flask server to see results here")
            else:
                st.warning("⚠️ Please ensure Flask server is running and try refreshing the page")


# Entry point when run directly
if __name__ == "__main__":
    ui = StreamlitUI()
    ui.run()

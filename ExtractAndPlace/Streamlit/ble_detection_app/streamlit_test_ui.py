"""Streamlit Test UI for debugging and testing the BLE detection system."""

import streamlit as st
import requests
import time
import io
import base64
import numpy as np
from PIL import Image
import logging
import sys
import os

# Ensure we can import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from image_utils import ImageProcessor
from config import FLASK_PORT, CLASS_ID


class StreamlitTestUI:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.flask_url = f"http://localhost:{FLASK_PORT}"
        self.server_running = False
        
        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for test mode."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def check_server_status(self):
        """Check if Flask server is running."""
        try:
            response = requests.get(f"{self.flask_url}/status", timeout=2)
            self.logger.info(f"Server status check: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Server status check failed: {e}")
            return False

    def setup_page(self):
        """Setup Streamlit page configuration for test mode."""
        st.set_page_config(
            page_title="BLE Detection Test & Debug",
            page_icon="🧪",
            layout="wide"
        )
        
        st.title("🧪 BLE Detection Test & Debug Console")
        st.markdown("**Debug mode - All testing and logging features enabled**")
        st.markdown(f"**Flask Server:** `{self.flask_url}`")
        
        # Warning banner
        st.warning("⚠️ This is the test interface with full logging and debug features")

    def display_logging_console(self):
        """Display logging information and console."""
        st.header("📝 Logging Console")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Logging Controls")
            log_level = st.selectbox(
                "Log Level", 
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=0
            )
            
            if st.button("🔄 Update Log Level"):
                getattr(logging, log_level.upper())
                st.success(f"Log level set to {log_level}")
            
            if st.button("📋 Show Current Logs"):
                # This would show recent logs if we had a log handler
                st.info("Log display feature - would show recent application logs")
        
        with col2:
            st.subheader("🔍 System Info")
            st.write(f"**Python Version:** {sys.version}")
            st.write(f"**Current Working Dir:** {os.getcwd()}")
            st.write(f"**Flask URL:** {self.flask_url}")
            st.write(f"**Server Status:** {'🟢 Online' if self.server_running else '🔴 Offline'}")

    def detailed_server_diagnostics(self):
        """Detailed server diagnostics and testing."""
        st.header("🔬 Server Diagnostics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🌐 Connection Tests")
            
            if st.button("🔗 Test Basic Connection"):
                with st.spinner("Testing basic connection..."):
                    try:
                        response = requests.get(f"{self.flask_url}/status", timeout=5)
                        st.success("✅ Basic connection successful")
                        st.json(response.json())
                        self.logger.info("Basic connection test passed")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")
                        self.logger.error(f"Basic connection test failed: {e}")
            
            if st.button("📊 Get Server Status"):
                try:
                    response = requests.get(f"{self.flask_url}/status", timeout=5)
                    data = response.json()
                    st.success("✅ Status retrieved")
                    st.json(data)
                    
                    # Log detailed status
                    self.logger.info(f"Server status: {data}")
                    
                except Exception as e:
                    st.error(f"❌ Status request failed: {e}")
                    self.logger.error(f"Status request failed: {e}")
        
        with col2:
            st.subheader("📡 BLE Diagnostics")
            
            if st.button("🔍 Check BLE Ready"):
                try:
                    response = requests.get(f"{self.flask_url}/ready", timeout=5)
                    data = response.json()
                    
                    if data.get('ready', False):
                        st.success("✅ BLE Arm is ready")
                    else:
                        st.warning("⏳ BLE Arm is busy")
                    
                    st.json(data)
                    self.logger.info(f"BLE ready status: {data}")
                    
                except Exception as e:
                    st.error(f"❌ BLE check failed: {e}")
                    self.logger.error(f"BLE check failed: {e}")
            
            if st.button("🔄 Detailed BLE Status"):
                try:
                    response = requests.get(f"{self.flask_url}/status", timeout=5)
                    data = response.json()
                    ble_status = data.get('ble_status', {})
                    
                    st.write("**BLE Detailed Status:**")
                    st.json(ble_status)
                    self.logger.info(f"Detailed BLE status: {ble_status}")
                    
                except Exception as e:
                    st.error(f"❌ Detailed BLE check failed: {e}")
                    self.logger.error(f"Detailed BLE check failed: {e}")
        
        with col3:
            st.subheader("🗃️ Data Operations")
            
            if st.button("📥 Get Current Data"):
                try:
                    response = requests.get(f"{self.flask_url}/get", timeout=5)
                    data = response.json()
                    st.success("✅ Data retrieved")
                    st.json(data)
                    self.logger.info(f"Current data: {data}")
                    
                except Exception as e:
                    st.error(f"❌ Data retrieval failed: {e}")
                    self.logger.error(f"Data retrieval failed: {e}")
            
            if st.button("🗑️ Clear All Data"):
                try:
                    response = requests.post(f"{self.flask_url}/clear", timeout=5)
                    st.success("✅ Data cleared")
                    self.logger.info("Data cleared successfully")
                    
                except Exception as e:
                    st.error(f"❌ Clear operation failed: {e}")
                    self.logger.error(f"Clear operation failed: {e}")

    def advanced_test_data_sender(self):
        """Advanced test data sending capabilities."""
        st.header("🧪 Advanced Test Data Sender")
        
        tab1, tab2, tab3 = st.tabs(["Single Test", "Batch Tests", "Custom Scenarios"])
        
        with tab1:
            st.subheader("📤 Single Test Detection")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Test data configuration
                test_object = st.selectbox(
                    "Test Object", 
                    ["cube", "triangle", "rectangle", "arch", "cylinder", "half_circle"]
                )
                
                confidence = st.slider("Confidence", 0.1, 1.0, 0.95, 0.01)
                
                # Position controls
                st.subheader("Position")
                x_pos = st.slider("X Position", 0, 640, 320)
                y_pos = st.slider("Y Position", 0, 480, 240)
                
                # Crop shape controls
                st.subheader("Crop Shape")
                crop_width = st.slider("Crop Width", 100, 1920, 640)
                crop_height = st.slider("Crop Height", 100, 1080, 480)
                
                # Advanced options
                st.subheader("Advanced Options")
                include_image = st.checkbox("Include Test Image", value=True)
                custom_timestamp = st.checkbox("Custom Timestamp", value=False)
                
                if custom_timestamp:
                    timestamp_offset = st.slider("Timestamp Offset (seconds)", -3600, 3600, 0)
                else:
                    timestamp_offset = 0
            
            with col2:
                st.subheader("📊 Test Results")
                
                if st.button("📤 Send Test Detection", type="primary"):
                    if self.server_running:
                        # Create test data
                        test_data = self.create_test_data(
                            test_object, confidence, x_pos, y_pos, 
                            crop_width, crop_height, include_image, timestamp_offset
                        )
                        
                        # Send and log
                        result = self.send_test_data(test_data)
                        
                        if result:
                            st.success("✅ Test data sent successfully")
                            st.json(result)
                            
                            # Show BLE commands
                            st.info("📡 BLE Commands that would be sent:")
                            st.code(f"S {crop_width} {crop_height}")
                            obj_id = CLASS_ID.get(test_object, 1)
                            st.code(f"T {x_pos} {y_pos} {obj_id}")
                        else:
                            st.error("❌ Test data sending failed")
                    else:
                        st.error("❌ Server not connected")
        
        with tab2:
            st.subheader("🔄 Batch Testing")
            
            num_tests = st.slider("Number of Tests", 1, 10, 3)
            delay_between = st.slider("Delay Between Tests (seconds)", 0.1, 5.0, 1.0)
            
            if st.button("🚀 Run Batch Tests"):
                if self.server_running:
                    self.run_batch_tests(num_tests, delay_between)
                else:
                    st.error("❌ Server not connected")
        
        with tab3:
            st.subheader("🎭 Custom Test Scenarios")
            
            scenario = st.selectbox(
                "Test Scenario",
                [
                    "Multiple Objects",
                    "High Confidence Objects", 
                    "Low Confidence Objects",
                    "Edge Position Objects",
                    "Large Crop Area",
                    "Small Crop Area"
                ]
            )
            
            if st.button("▶️ Run Scenario"):
                if self.server_running:
                    self.run_test_scenario(scenario)
                else:
                    st.error("❌ Server not connected")

    def create_test_data(self, obj_class, confidence, x, y, crop_w, crop_h, include_image=True, timestamp_offset=0):
        """Create test data payload."""
        test_data = {
            "detections": [
                {
                    "class": obj_class,
                    "confidence": confidence,
                    "center_px": [x, y]
                }
            ],
            "crop_shape": [crop_w, crop_h],
            "timestamp": time.time() + timestamp_offset
        }
        
        if include_image:
            # Create a simple test image
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            test_data["image"] = img_base64
        
        self.logger.debug(f"Created test data: {test_data}")
        return test_data

    def send_test_data(self, test_data):
        """Send test data to server."""
        try:
            self.logger.info("Sending test data to server...")
            response = requests.post(
                f"{self.flask_url}/data", 
                json=test_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Test data sent successfully: {result}")
                return result
            else:
                self.logger.error(f"Test data sending failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Exception while sending test data: {e}")
            return None

    def run_batch_tests(self, num_tests, delay):
        """Run batch tests."""
        st.info(f"Running {num_tests} batch tests...")
        
        test_objects = ["cube", "triangle", "rectangle", "arch", "cylinder", "half_circle"]
        progress_bar = st.progress(0)
        
        for i in range(num_tests):
            obj = test_objects[i % len(test_objects)]
            
            test_data = self.create_test_data(
                obj, 0.9 + (i * 0.01), 
                300 + (i * 20), 200 + (i * 15),
                640, 480
            )
            
            result = self.send_test_data(test_data)
            
            if result:
                st.success(f"✅ Test {i+1}/{num_tests} ({obj}) completed")
            else:
                st.error(f"❌ Test {i+1}/{num_tests} ({obj}) failed")
            
            progress_bar.progress((i + 1) / num_tests)
            time.sleep(delay)
        
        st.success("🎉 Batch tests completed!")

    def run_test_scenario(self, scenario):
        """Run specific test scenarios."""
        st.info(f"Running scenario: {scenario}")
        
        if scenario == "Multiple Objects":
            # Send multiple objects in one detection
            test_data = {
                "detections": [
                    {"class": "cube", "confidence": 0.95, "center_px": [200, 200]},
                    {"class": "triangle", "confidence": 0.87, "center_px": [400, 300]},
                    {"class": "rectangle", "confidence": 0.92, "center_px": [300, 250]}
                ],
                "crop_shape": [640, 480],
                "timestamp": time.time()
            }
            
        elif scenario == "High Confidence Objects":
            test_data = self.create_test_data("cube", 0.99, 320, 240, 640, 480)
            
        elif scenario == "Low Confidence Objects":
            test_data = self.create_test_data("triangle", 0.35, 320, 240, 640, 480)
            
        elif scenario == "Edge Position Objects":
            test_data = self.create_test_data("rectangle", 0.90, 50, 50, 640, 480)
            
        elif scenario == "Large Crop Area":
            test_data = self.create_test_data("arch", 0.88, 960, 540, 1920, 1080)
            
        elif scenario == "Small Crop Area":
            test_data = self.create_test_data("cylinder", 0.85, 160, 120, 320, 240)
        
        result = self.send_test_data(test_data)
        if result:
            st.success(f"✅ Scenario '{scenario}' completed successfully")
            st.json(result)
        else:
            st.error(f"❌ Scenario '{scenario}' failed")

    def display_live_monitoring(self):
        """Display live monitoring of server data."""
        st.header("📊 Live Monitoring")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_refresh = st.checkbox("Auto Refresh", value=False)
            refresh_rate = st.slider("Refresh Rate (s)", 0.5, 5.0, 1.0)
        
        with col2:
            if st.button("🔄 Manual Refresh"):
                st.rerun()
        
        # Display area
        status_placeholder = st.empty()
        data_placeholder = st.empty()
        
        if auto_refresh and self.server_running:
            # Auto refresh logic
            for i in range(20):  # Limit iterations
                try:
                    response = requests.get(f"{self.flask_url}/get", timeout=3)
                    data = response.json()
                    
                    status_placeholder.success(f"✅ Live data - Refresh #{i+1}")
                    data_placeholder.json(data)
                    
                    self.logger.debug(f"Live monitoring refresh {i+1}: {data}")
                    
                except Exception as e:
                    status_placeholder.error(f"❌ Refresh error: {e}")
                    self.logger.error(f"Live monitoring error: {e}")
                
                time.sleep(refresh_rate)
        else:
            # Manual refresh
            if self.server_running:
                try:
                    response = requests.get(f"{self.flask_url}/get", timeout=3)
                    data = response.json()
                    
                    status_placeholder.success("✅ Data retrieved")
                    data_placeholder.json(data)
                    
                except Exception as e:
                    status_placeholder.error(f"❌ Error: {e}")
            else:
                status_placeholder.warning("⚠️ Server not connected")

    def run(self):
        """Run the test UI."""
        self.setup_page()
        
        # Check server initially
        self.server_running = self.check_server_status()
        
        # Server status indicator
        if self.server_running:
            st.success(f"✅ Connected to Flask server at {self.flask_url}")
        else:
            st.error(f"❌ Cannot connect to Flask server at {self.flask_url}")
            st.stop()
        
        # Logging console
        self.display_logging_console()
        
        # Detailed diagnostics
        self.detailed_server_diagnostics()
        
        # Advanced test sender
        self.advanced_test_data_sender()
        
        # Live monitoring
        self.display_live_monitoring()


# Entry point when run directly
if __name__ == "__main__":
    test_ui = StreamlitTestUI()
    test_ui.run()

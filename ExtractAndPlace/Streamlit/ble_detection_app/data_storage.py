"""Data storage and management for detection results."""

import threading
from typing import Dict, List, Optional
import time


class DataStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_data = {}
        self._detection_history = []
        self._max_history = 100

    def store_data(self, data: Dict):
        """Store the latest detection data."""
        with self._lock:
            data['timestamp'] = time.time()
            self._latest_data = data
            self._detection_history.append(data)
            
            # Keep only recent history
            if len(self._detection_history) > self._max_history:
                self._detection_history.pop(0)

    def get_latest_data(self) -> Dict:
        """Get the most recent detection data."""
        with self._lock:
            return self._latest_data.copy()

    def get_detection_count(self) -> int:
        """Get the number of detections in latest data."""
        with self._lock:
            return len(self._latest_data.get('detections', []))

    def get_history(self) -> List[Dict]:
        """Get detection history."""
        with self._lock:
            return self._detection_history.copy()

    def clear_data(self):
        """Clear all stored data."""
        with self._lock:
            self._latest_data = {}
            self._detection_history = []


# Global data storage instance
data_store = DataStorage()

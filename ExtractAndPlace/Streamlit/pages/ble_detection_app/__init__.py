"""BLE Detection Application Package."""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "BLE Detection Application with Flask and Streamlit"

# Import main components for easy access
try:
    from .flask_server import flask_server, app
    from .ble_handler import BLEHandler
    from .data_storage import data_store
    from .config import *
    
    __all__ = [
        'flask_server',
        'app', 
        'BLEHandler',
        'data_store',
        'CLASS_ID',
        'FLASK_HOST',
        'FLASK_PORT'
    ]
except ImportError:
    # If imports fail, just define the package
    pass

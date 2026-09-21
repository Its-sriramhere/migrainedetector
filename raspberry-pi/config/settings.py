import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEVICE_ID = os.getenv("DEVICE_ID", "PI-001")
DEVICE_NAME = os.getenv("DEVICE_NAME", "Raspberry Pi")
UPLOAD_INTERVAL = float(os.getenv("UPLOAD_INTERVAL", "10"))
HEARTBEAT_INTERVAL = float(os.getenv("HEARTBEAT_INTERVAL", "60"))
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
DEMO_SOURCE_ENABLED = os.getenv("DEMO_SOURCE", "1") == "1"
DEMO_INTERVAL = float(os.getenv("DEMO_INTERVAL", "5"))
LOCAL_DB = os.getenv("LOCAL_DB", "pi_data.db")
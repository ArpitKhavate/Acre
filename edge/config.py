"""Edge configuration for the Acre handheld scanner.

Everything here is local to the device. Override via environment variables so
the same code runs on a dev laptop (stub backends) and the Pi 5 (real GPIO).
"""
import os
from pathlib import Path

EDGE_DIR = Path(__file__).parent
MODELS_DIR = EDGE_DIR.parent / "models"
ARTIFACTS_DIR = MODELS_DIR / "artifacts"
LABELS_DIR = MODELS_DIR / "labels"

# --- Identity -------------------------------------------------------------
DEVICE_ID = os.environ.get("ACRE_DEVICE_ID", "acre-01")
FARM_ID = os.environ.get("ACRE_FARM_ID", "demo-farm-1")

# --- Storage --------------------------------------------------------------
DB_PATH = Path(os.environ.get("ACRE_DB_PATH", str(EDGE_DIR / "acre_local.db")))
IMAGE_DIR = Path(os.environ.get("ACRE_IMAGE_DIR", str(EDGE_DIR / "captures")))
ZONES_CONFIG = Path(os.environ.get("ACRE_ZONES", str(EDGE_DIR / "config" / "zones.json")))

# --- Models ---------------------------------------------------------------
DETECTOR_ONNX = ARTIFACTS_DIR / "detector.onnx"
DISEASE_ONNX = ARTIFACTS_DIR / "disease.onnx"
PEST_ONNX = ARTIFACTS_DIR / "pest.onnx"

# --- Health score / LED ---------------------------------------------------
# Plant turns the LED GREEN at or above this score, otherwise RED. (PRD 9.2)
HEALTH_THRESHOLD = float(os.environ.get("ACRE_HEALTH_THRESHOLD", "70"))
DETECTION_CONF = float(os.environ.get("ACRE_DETECTION_CONF", "0.35"))

# --- GPIO pins (BCM numbering) -------------------------------------------
LED_RED_PIN = int(os.environ.get("ACRE_LED_RED_PIN", "17"))
LED_GREEN_PIN = int(os.environ.get("ACRE_LED_GREEN_PIN", "27"))
LED_BLUE_PIN = int(os.environ.get("ACRE_LED_BLUE_PIN", "23"))  # optional: syncing
BUZZER_PIN = int(os.environ.get("ACRE_BUZZER_PIN", "22"))

# --- Sync -----------------------------------------------------------------
BACKEND_URL = os.environ.get("ACRE_BACKEND_URL", "http://localhost:8000/api/sync")
SYNC_INTERVAL_S = int(os.environ.get("ACRE_SYNC_INTERVAL_S", "30"))
SYNC_BATCH_SIZE = int(os.environ.get("ACRE_SYNC_BATCH_SIZE", "50"))

# --- Camera ---------------------------------------------------------------
CAMERA_INDEX = int(os.environ.get("ACRE_CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.environ.get("ACRE_FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.environ.get("ACRE_FRAME_HEIGHT", "480"))

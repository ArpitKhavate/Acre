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
TREATMENTS_CONFIG = Path(os.environ.get(
    "ACRE_TREATMENTS", str(EDGE_DIR / "config" / "treatments.json")))
REPORTS_DIR = Path(os.environ.get("ACRE_REPORTS_DIR", str(EDGE_DIR / "reports")))
# Trailing window (hours) of scans that count toward the on-device report.
REPORT_WINDOW_HOURS = float(os.environ.get("ACRE_REPORT_WINDOW_HOURS", "24"))

# --- Models ---------------------------------------------------------------
DETECTOR_ONNX = ARTIFACTS_DIR / "detector.onnx"
DISEASE_ONNX = ARTIFACTS_DIR / "disease.onnx"
PEST_ONNX = ARTIFACTS_DIR / "pest.onnx"

# --- Health score / LED ---------------------------------------------------
# Plant turns the LED GREEN at or above this score, otherwise RED. (PRD 9.2)
HEALTH_THRESHOLD = float(os.environ.get("ACRE_HEALTH_THRESHOLD", "70"))
DETECTION_CONF = float(os.environ.get("ACRE_DETECTION_CONF", "0.55"))
DETECTION_NMS_IOU = float(os.environ.get("ACRE_DETECTION_NMS_IOU", "0.40"))
# Reject boxes that are tiny slivers or lack plant-like green (filters people/walls).
DETECTION_MIN_BOX_AREA = float(os.environ.get("ACRE_DETECTION_MIN_BOX_AREA", "0.06"))
DETECTION_MIN_GREEN_RATIO = float(os.environ.get("ACRE_DETECTION_MIN_GREEN_RATIO", "0.10"))
# Classifiers only apply when confidence exceeds this (avoids random labels on background).
CLASSIFIER_MIN_CONF = float(os.environ.get("ACRE_CLASSIFIER_MIN_CONF", "0.55"))

# --- GPIO pins (BCM numbering) -------------------------------------------
LED_RED_PIN = int(os.environ.get("ACRE_LED_RED_PIN", "17"))
LED_GREEN_PIN = int(os.environ.get("ACRE_LED_GREEN_PIN", "27"))
LED_BLUE_PIN = int(os.environ.get("ACRE_LED_BLUE_PIN", "23"))  # optional: syncing
LASER_PIN = int(os.environ.get("ACRE_LASER_PIN", "24"))        # digital on/off

# Buzzer is NOT part of this build; off by default. Enable only if you wire one.
BUZZER_ENABLED = os.environ.get("ACRE_BUZZER_ENABLED", "0") == "1"
BUZZER_PIN = int(os.environ.get("ACRE_BUZZER_PIN", "22"))

# --- Servo (pan axis for laser aiming, PRD 7.1) --------------------------
# Set ACRE_SERVO_ENABLED=0 to run the whole pipeline without a servo wired:
# the aiming logic still runs and prints its target angles (stub), the laser
# and everything else stay real, but no PWM pin is driven.
SERVO_ENABLED = os.environ.get("ACRE_SERVO_ENABLED", "1") == "1"
# Hardware-PWM pins on the Pi 5 / QNX rpi_gpio module: 12, 18 (ch1), 13, 19 (ch2).
SERVO_PWM_PIN = int(os.environ.get("ACRE_SERVO_PWM_PIN", "18"))
SERVO_FREQ_HZ = int(os.environ.get("ACRE_SERVO_FREQ_HZ", "50"))
SERVO_MIN_ANGLE = float(os.environ.get("ACRE_SERVO_MIN_ANGLE", "0"))
SERVO_MAX_ANGLE = float(os.environ.get("ACRE_SERVO_MAX_ANGLE", "180"))
SERVO_CENTER_ANGLE = float(os.environ.get("ACRE_SERVO_CENTER_ANGLE", "90"))
# Pulse width (ms) at min/max angle for a typical hobby servo; duty = pulse/period.
SERVO_MIN_PULSE_MS = float(os.environ.get("ACRE_SERVO_MIN_PULSE_MS", "0.5"))
SERVO_MAX_PULSE_MS = float(os.environ.get("ACRE_SERVO_MAX_PULSE_MS", "2.5"))
# Proportional gain converting pixel x-error to angle correction (PRD 7.1).
SERVO_GAIN = float(os.environ.get("ACRE_SERVO_GAIN", "0.05"))
# How many correction iterations per lock-on, and how centered counts as "locked".
AIM_MAX_STEPS = int(os.environ.get("ACRE_AIM_MAX_STEPS", "6"))
AIM_TOLERANCE_PX = int(os.environ.get("ACRE_AIM_TOLERANCE_PX", "20"))

# --- Humiture (DHT11, single-wire, PRD 6) --------------------------------
HUMITURE_PIN = int(os.environ.get("ACRE_HUMITURE_PIN", "26"))
# DHT11 reads are timing-marginal; throttle to avoid hammering the sensor.
HUMITURE_MIN_INTERVAL_S = float(os.environ.get("ACRE_HUMITURE_MIN_INTERVAL_S", "2.0"))

# --- LCD (I2C 1602, PCF8574 backpack) ------------------------------------
# On QNX the bus is exposed by i2c-dwc-rpi5 as /dev/i2c1; on Linux it's an int.
LCD_I2C_BUS = os.environ.get("ACRE_LCD_I2C_BUS", "/dev/i2c1")
LCD_I2C_ADDR = int(os.environ.get("ACRE_LCD_I2C_ADDR", "0x27"), 0)
LCD_ENABLED = os.environ.get("ACRE_LCD_ENABLED", "1") == "1"

# --- Sync -----------------------------------------------------------------
BACKEND_URL = os.environ.get("ACRE_BACKEND_URL", "http://localhost:8000/api/sync")
SYNC_INTERVAL_S = int(os.environ.get("ACRE_SYNC_INTERVAL_S", "30"))
SYNC_BATCH_SIZE = int(os.environ.get("ACRE_SYNC_BATCH_SIZE", "50"))
# Cloud endpoint to refresh the farm report after syncing. Empty = derive it
# from BACKEND_URL (.../api/sync -> .../api/farms/<farm>/report).
CLOUD_REPORT_URL = os.environ.get("ACRE_CLOUD_REPORT_URL", "")

# --- Camera ---------------------------------------------------------------
CAMERA_INDEX = int(os.environ.get("ACRE_CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.environ.get("ACRE_FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.environ.get("ACRE_FRAME_HEIGHT", "480"))

# QNX bridge / manual testing: read frames from a folder (newest image) or a
# single file instead of a live camera. On QNX, point a camera capture tool at
# ACRE_FRAME_DIR so this Python pipeline picks up each new JPEG. Leave unset to
# use a live camera (picamera2 / OpenCV).
FRAME_DIR = os.environ.get("ACRE_FRAME_DIR", "")
FRAME_FILE = os.environ.get("ACRE_FRAME_FILE", "")

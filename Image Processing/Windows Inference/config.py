"""
Configuration file for the object detector.
Modify values here instead of inside detector.py.
"""

# ----------------------------
# Camera
# ----------------------------

CAMERA_INDEX = 1

# ----------------------------
# Detection
# ----------------------------

DETECTION_TIME = 5.0               # seconds
CONFIDENCE_THRESHOLD = 0.60
REQUIRED_CONSECUTIVE_DETECTIONS = 3

# ----------------------------
# YOLO
# ----------------------------

MODEL_PATH = "weights/best.pt"

# ----------------------------
# Debug
# ----------------------------

# PRINT_STATUS = True

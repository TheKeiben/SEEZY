"""
test_detector.py

Simple program for testing detector.py
"""

import logging

from ultralytics import YOLO

from config import MODEL_PATH
from detector import detect_item


# --------------------------------------------------
# Configure logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s"
)

# --------------------------------------------------
# Load YOLO model (only once)
# --------------------------------------------------

model = YOLO(MODEL_PATH)

# --------------------------------------------------
# Run detector
# --------------------------------------------------

detect_item(
    model=model,
    item_id=0,
    camera_angle=0.0
)
"""
detector.py

Object detection algorithm.

Workflow:

Robot Navigation
        │
        ▼
detect_item(item_id, camera_angle)
        │
        ▼
Move servo (future)
        │
        ▼
Open camera
        │
        ▼
Run YOLO
        │
        ▼
Found?
    │         │
   Yes        No
    │         │
    ▼         ▼
Print      Timeout?
Success      │
             ▼
         Print Failure
"""

import logging
import time
import cv2

from config import (
    CAMERA_INDEX,
    DETECTION_TIME,
    CONFIDENCE_THRESHOLD,
    REQUIRED_CONSECUTIVE_DETECTIONS,
)

from items import ITEMS

logger = logging.getLogger(__name__)


def detect_item(model, item_id: int, camera_angle: float) -> None:
    """
    Detect a requested object.

    Parameters
    ----------
    model : YOLO
        Loaded YOLO model.

    item_id : int
        Requested item ID.

    camera_angle : float
        Desired servo angle.
        (Reserved for future implementation.)

    Returns
    -------
    None
    """

    # --------------------------------------------------
    # Validate requested item
    # --------------------------------------------------

    if item_id not in ITEMS:
        logger.error(f"Unknown item ID: {item_id}")
        return

    target_name = ITEMS[item_id]

    # --------------------------------------------------
    # Move servo (future implementation)
    # --------------------------------------------------

    # servo.move(camera_angle)

    # --------------------------------------------------
    # Open camera
    # --------------------------------------------------

    logger.info("Opening camera...")
    start_time = time.time()

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        logger.error("Could not open camera.")
        return
    else:
        logger.info(f"Camera opened after: {time.time()-start_time} seconds")
    
    logger.info("----------------------------------------")
    logger.info("Starting object detection")
    logger.info(f"Target Item : {target_name}")
    logger.info(f"Timeout     : {DETECTION_TIME:.1f} seconds")
    logger.info(f"Confidence  : {CONFIDENCE_THRESHOLD:.2f}")
    logger.info("----------------------------------------")

    start_time = time.time()
    consecutive_detections = 0

    try:

        while True:

            success, frame = cap.read()

            if not success:
                logger.error("Failed to read camera frame.")
                break

            elapsed = time.time() - start_time

            # Check timeout
            if elapsed >= DETECTION_TIME:
                logger.warning("----------------------------------------")
                logger.warning("[FAILED]")
                logger.warning(
                    f"'{target_name}' was not detected within "
                    f"{DETECTION_TIME:.1f} seconds."
                )
                logger.warning("----------------------------------------")
                break

            # Run YOLO inference
            results = model.predict(
                frame,
                verbose=False
            )

            detected = False
            detected_confidence = 0.0

            # Search detections
            for result in results:

                for box in result.boxes:

                    class_index = int(box.cls[0])
                    class_name = model.names[class_index]
                    confidence = float(box.conf[0])

                    if (
                        class_name == target_name
                        and confidence >= CONFIDENCE_THRESHOLD
                    ):
                        detected = True
                        detected_confidence = confidence
                        break

                if detected:
                    break

            # Consecutive detection logic
            if detected:
                consecutive_detections += 1
            else:
                consecutive_detections = 0

            # Stable detection achieved
            if consecutive_detections >= REQUIRED_CONSECUTIVE_DETECTIONS:

                logger.info("----------------------------------------")
                logger.info("[SUCCESS]")
                logger.info(f"Detected Item : {target_name}")
                logger.info(f"Confidence    : {detected_confidence:.2f}")
                logger.info(f"Elapsed Time  : {elapsed:.2f} seconds")
                logger.info(
                    f"Stable Frames : "
                    f"{REQUIRED_CONSECUTIVE_DETECTIONS}"
                )
                logger.info("----------------------------------------")

                break

    finally:

        cap.release()

        logger.info("Camera released.")
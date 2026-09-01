from ultralytics import YOLO
import cv2
import time
import os

# ----------------------------
# Configuration
# ----------------------------

MODEL_PATH = "weights/best.pt"

CONFIDENCE = 0.80

# ----------------------------
# Load model
# ----------------------------

print("Loading model...")

model = YOLO(MODEL_PATH)

print("Model loaded.")

# ----------------------------
# Open webcam
# ----------------------------

cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Could not open webcam.")
    exit()

print("Press Q to quit.")

prev_time = time.time()

# ----------------------------
# Main loop
# ----------------------------

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Run inference
    results = model.predict(
        frame,
        conf=CONFIDENCE,
        verbose=False
    )

    # Draw detections
    annotated = results[0].plot()

    # FPS calculation
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    cv2.putText(
        annotated,
        f"FPS: {fps:.1f}",
        (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("YOLO Live Detection", annotated)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ----------------------------
# Cleanup
# ----------------------------

cap.release()
cv2.destroyAllWindows()
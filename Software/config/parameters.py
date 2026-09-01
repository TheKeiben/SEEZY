"""
SEEZY Project - Master System Parameters & Global Configuration
All numerical thresholds, timeouts, device paths, and topic names are centralized here.
"""

import os

# ==========================================
# 1. HARDWARE & DEVICE PORTS
# ==========================================
ESP_PORT_DEFAULT = "/dev/seezy_esp"
LIDAR_PORT_DEFAULT = "/dev/seezy_lidar"
PORT_FALLBACK_OPTIONS = ["/dev/seezy_esp", "/dev/seezy_lidar", "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyACM0"]

CAMERA_DEVICE = "/dev/video0"
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# ==========================================
# 2. PERCEPTION & YOLO TUNING
# ==========================================
MODEL_FILENAME = "yolov8n_res640.engine"
YOLO_CONFIDENCE_THRESHOLD = 0.60
REQUIRED_DETECTION_STREAK = 3          # Consecutive frames required to confirm an item
DETECTION_TIMEOUT_MS = 15000           # 15.0 seconds before skipping an undetected item

# Supermarket Product Classes Mapping
CLASS_NAMES = {
    0: "milk_3p_tnuva",
    1: "ketchup_heinz",
    2: "bamba_osem",
    3: "cafe_names_elit",
    4: "toothpaste_colgate"
}

# ==========================================
# 3. MANUAL DRIVING VELOCITIES (m/s & rad/s)
# ==========================================
MANUAL_LINEAR_SPEED = 0.20             # Forward / Backward velocity
MANUAL_ANGULAR_SPEED = 0.50            # Left / Right rotational velocity

MANUAL_SPEED_MAP = {
    "FORWARD": (MANUAL_LINEAR_SPEED, 0.0),
    "BACKWARD": (-MANUAL_LINEAR_SPEED, 0.0),
    "LEFT": (0.0, MANUAL_ANGULAR_SPEED),
    "RIGHT": (0.0, -MANUAL_ANGULAR_SPEED)
}

# ==========================================
# 4. TELEMETRY & HEARTBEAT TIMEOUTS
# ==========================================
TELEMETRY_TIMEOUT_SEC = 3.0            # Seconds before a topic is marked disconnected
HEALTH_TIMER_FREQ_HZ = 1.0             # Periodic telemetry evaluation rate
NAV2_SERVER_TIMEOUT_SEC = 3.0          # Action server availability timeout

# ==========================================
# 5. ROS 2 TOPICS & ACTION INTERFACES
# ==========================================
TOPIC_CMD_VEL = "/cmd_vel"
TOPIC_SCAN = "/scan"
TOPIC_ODOM = "/odom"
TOPIC_ENCODER_LEFT = "/encoder/left"
TOPIC_VISION_DETECTIONS = "/seezy/detections"
TOPIC_VISION_ANNOTATED = "/seezy/camera/annotated"
TOPIC_VISION_HEALTH = "/seezy/vision_health"
TOPIC_SET_CONFIDENCE = "/seezy/set_confidence"
SERVICE_RESET_ESP = "/seezy/reset_esp"
ACTION_NAVIGATE_TO_POSE = "/navigate_to_pose"

# ==========================================
# 6. SYSTEM PATHS & SCRIPTS
# ==========================================
ROS2_SETUP_SCRIPT = os.path.expanduser("~/SEEZY/ROS2/dev/ver1-1-01/install/setup.bash")
ROS2_LAUNCH_PACKAGE = "bringup"
ROS2_LAUNCH_FILE = "ros2_launch.py"
================================================================================
SEEZY Software Module (System Controller) README
================================================================================

Directory Overview
------------------
This directory houses the central control and monitoring application for the SEEZY robotic platform[cite: 19]. It is a highly decoupled, multi-threaded PyQt6 Python system designed to act as the "master brain"[cite: 17]. It orchestrates the user interface, manages the algorithmic shopping queue, safely spawns ROS 2 hardware processes, and bridges communications between the YOLO perception node and the Nav2 autonomous driving stack[cite: 17, 18].

File & Subdirectory Overview
----------------------------
* main.py: The central entry point. Initializes the PyQt6 application, sets up the logger, and instantiates the MainWindow and SystemController[cite: 12, 17].
* launch/launch.sh: The master bash script used to grant USB udev permissions, activate the Python virtual environment, source ROS 2, and boot the application[cite: 10, 15].
* config/: 
  - parameters.py: A centralized configuration file holding all numerical constants, device ports, thresholds, speeds, and ROS 2 topic names to prevent hardcoding[cite: 9, 20].
  - locations.yaml: Stores the spatial coordinates (x, y, theta) for supermarket shelves and the checkout counter[cite: 8, 20].
* controller/: 
  - system_controller.py: The master state machine. Routes logic between the UI, the robot thread, and the buying session. Handles subprocess launching for the hardware and vision nodes[cite: 17, 18].
  - buying_session.py: The algorithmic shopping manager tracking the active queue, completed items, and step-by-step navigation logic[cite: 6, 17, 18].
  - state_manager.py: Contains Enum classes mapping the Session, Operating Mode, and System Status states[cite: 7].
* perception/: 
  - vision_node.py: An isolated script launched as a background subprocess. It runs the YOLOv8 TensorRT engine using a V4L2 webcam feed and publishes JSON detection payloads to the ROS 2 network[cite: 16, 20].
* robot/: 
  - robot_controller.py: The ROS 2 middleware bridge running on a dedicated QThread. Hosts `SeezyCoreNode` to send `/cmd_vel` Twist commands, dispatch goals to the Nav2 Action Server, and track sensor heartbeats[cite: 11, 17, 18].
* ui/: 
  - main_window.py: The graphical dashboard. Contains port dropdowns, dynamic subsystem health indicators, a live YOLO confidence slider, shopping queue visualizer, and hardware keypress routing for manual drive/E-stops[cite: 15, 17].
* utils/: 
  - audio_manager.py: An asynchronous text-to-speech engine running on a background thread so audio announcements never freeze the PyQt UI[cite: 13, 17].
  - logging_config.py: A custom logging handler mapping standard Python logs to a Qt Signal for the live UI log panel[cite: 14, 15].

Setup & Installation
--------------------
* Requires Ubuntu 24.04, ROS 2 Jazzy, Python 3.12, and PyQt6[cite: 17].
* Requires permanent Linux `udev` rules securely locking the ESP32 to `/dev/seezy_esp` and the LiDAR to `/dev/seezy_lidar`[cite: 17]. 
* Ensure the Python virtual environment (`venv`) has access to global system site-packages for ROS 2 (`rclpy`) and OpenCV hardware bindings[cite: 12].

How to Use / Execution
----------------------
1. Do not run `main.py` directly if you need hardware access. Instead, execute `bash launch/launch.sh` (or a corresponding `.desktop` shortcut)[cite: 10, 15].
2. The UI boots into a DISCONNECTED state[cite: 17].
3. Click "LAUNCH ROS 2" to automatically boot both the Bumperbot base hardware stack (via subprocess) and the YOLO Vision node[cite: 17].
4. Wait for the Subsystem Health indicators (ESP32, ROS 2 Base, LiDAR, YOLO) to turn green (🟢)[cite: 17].
5. Press `[M]` to switch to AUTO mode, select items `[1-5]`, and the robot will begin autonomous navigation[cite: 17].

Dependencies & Interactions
---------------------------
* Architecture strictly separates UI and ROS 2 logic into separate QThreads to guarantee dashboard responsiveness[cite: 17].
* The `vision_node.py` is fully decoupled from the UI, operating strictly via ROS 2 topics (`/seezy/detections`) so heavy GPU inference does not block the main Qt thread[cite: 16, 17, 20].
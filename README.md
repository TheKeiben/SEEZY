# SEEZY: Autonomous Supermarket Assistant

![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![ROS 2 Jazzy](https://img.shields.io/badge/ROS_2-Jazzy-22314E?style=for-the-badge&logo=ros&logoColor=white)
![JetPack 7.2](https://img.shields.io/badge/NVIDIA-JetPack_7.2-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-UI_Dashboard-41CD52?style=for-the-badge&logo=python&logoColor=white)


![SEEZY Robot Hero Shot](docs/images/hero_shot.png)

![SEEZY Robot Internal Shot 1](docs/images/internal_shot1.png)

![SEEZY Robot Internal Shot 2](docs/images/internal_shot2.png)


## 🛒 Project Overview
**SEEZY** is an autonomous supermarket assistant robot designed to guide visually impaired customers. It navigates to requested items, detects them using a custom YOLOv8 model (trained on 5 specific classes: milk, ketchup, bamba, coffee, toothpaste), and safely guides the user to the checkout counter[cite: 16].

## ⚙️ Hardware Stack
The physical architecture relies on a master-slave processing configuration:
*   **Master Compute:** NVIDIA Jetson Orin Nano (8GB)[cite: 23].
*   **Motor Controller:** ESP32 Microcontroller (running a 50Hz micro-ROS hardware PID loop)[cite: 16, 21].
*   **Perception:** Logitech Brio 500 webcam (1280x720 HD).
*   **Navigation / SLAM:** SLLidar (360-degree 2D planar scan)[cite: 21].
*   **Chassis:** Pioneer 3-DX with dual DC drive motors and differential wheel base[cite: 21].

---

## 📂 Repository Architecture (The 4 Pillars)

![System Architecture](docs/images/architecture_diagram.png)

The project is divided into four strictly decoupled modules to guarantee UI responsiveness and hardware safety[cite: 16, 21]:

### 1. `software/` (System Controller & UI)
A decoupled, multi-threaded PyQt6 application that acts as the "master brain"[cite: 16]. It strictly separates the graphical presentation layer from the ROS 2 middleware (running on a dedicated `QThread`) to ensure the dashboard never freezes during heavy TensorRT inference or network latency[cite: 21].

### 2. `ros2_workspace/` (Robot Navigation & Bringup)
Contains the core ROS 2 Jazzy packages[cite: 23]. This includes the Nav2 stack, URDF 3D descriptions, SLAM mapping configurations, and the master launch files required for physical robot bringup.

### 3. `image_processing/` (Vision Pipeline Development)
The computer vision sandbox. While production inference runs via the `perception/vision_node.py` subprocess[cite: 21], this folder contains the development pipelines: Google Colab YOLOv8 training notebooks, local Windows testing scripts, and TensorRT (`.engine`) conversion tools[cite: 17, 24].

### 4. `esp32/` (Firmware)
Custom C++ firmware implementing a micro-ROS auto-reconnect Ping State Machine[cite: 16]. It constantly pings the Jetson over serial and zeroes the motors automatically if the ROS 2 connection drops[cite: 16].

---

## 🚀 Installation & Setup

### 1. System Requirements
*   **OS:** Ubuntu 24.04 LTS[cite: 21]
*   **Environment:** ROS 2 Jazzy, Python 3.12[cite: 21]

### 2. Udev Rules & Hardware Ports
For the hardware to launch reliably, persistent Linux `udev` rules must be applied to securely lock the hardware ports[cite: 23].
*   ESP32 maps to: `/dev/seezy_esp`[cite: 23]
*   LiDAR maps to: `/dev/seezy_lidar`[cite: 23]

### 3. Python Environment
Install the native audio engine (for asynchronous text-to-speech) and the Python dependencies:
```bash
sudo apt update && sudo apt install espeak
python3 -m venv venv
source venv/bin/activate
pip install -r software/requirements.txt


## 🎮 Execution & Controls

![SEEZY Dashboard](docs/images/dashboard_ui.png)

### Launching the System
1. Navigate to the `software` directory.
2. Launch the UI using your bash script (e.g., `./start_ui.sh` or `python3 main.py`).
3. Select your hardware ports for the ESP32 and LiDAR in the GUI dropdown menus.
4. Click **LAUNCH ROS 2** to safely orchestrate the hardware bringup. This action securely manages the ROS 2 background process group and launches the YOLO vision node subprocess[cite: 16, 20].
5. Wait for the Subsystem Health indicators (ROS 2 Base, YOLO Vision, LiDAR) to turn green (🟢), which confirms live telemetry is flowing[cite: 16].

### State Machine & Keyboard Mapping
The system enforces strict cross-mode safety locks via a three-tier state machine (Status, Session, Mode) to prevent conflicting commands[cite: 16].

| Key | Action | Mode Requirement |
| :--- | :--- | :--- |
| **`[1-5]`** | Select Items to add to the shopping queue[cite: 16, 20] | AUTO |
| **`[6]`** | Route to Checkout Counter[cite: 16, 20] | AUTO |
| **`[V]`** | Confirm Item Hand-off (Resumes route after successful detection)[cite: 16] | AUTO |
| **`[C] / [X]`** | Retry Scan / Skip & Remove Item (Used if detection times out)[cite: 16] | AUTO |
| **`[M]`** | Toggle between AUTO and MANUAL operating modes[cite: 16] | ANY |
| **`[W/A/S/D]`** | Manual Drive (Press and hold to move, release to silently stop)[cite: 16, 20] | MANUAL |
| **`[E]`** | Instant Motor Brake[cite: 16] | MANUAL |
| **`[F]`** | Freeze / Resume (Saves active Nav2 coordinates and pauses motion)[cite: 16, 20] | ANY |
| **`[SPACE] / [H]`** | Emergency Halt (1st Press - instantly cuts motors and kills Nav2 paths) <br> Reset System (2nd Press - clears the queue and resets to IDLE/MANUAL)[cite: 16, 20] | ANY |

================================================================================
Linux Edge Inference Module (Jetson Orin Nano) README
================================================================================

Directory Overview
------------------
This directory houses the production perception scripts designed specifically for the NVIDIA Jetson Orin Nano. It handles hardware-specific TensorRT optimization, rigorous performance benchmarking, and the ROS 2 vision node integration.

File Overview
-------------
* convert_engines.py: A subprocess wrapper script that locates the native `trtexec` compiler and converts `.onnx` models into highly optimized, half-precision (FP16) TensorRT `.engine` files.
* benchmark_jetson.py: A headless hardware profiling script. It runs inference loops without GUI overhead and logs pipeline latency, FPS, VRAM usage, and power draw to a CSV file.
* vision_node.py: The production ROS 2 perception node. It captures Logitech Brio 500 frames via V4L2, runs TensorRT inference in a background thread, and publishes results.

Setup & Installation
--------------------
* Must be run natively on Ubuntu 24.04 (JetPack 7.2 environment).
* Requires a virtual environment with the `--system-site-packages` flag enabled to access JetPack's native TensorRT and OpenCV bindings.
* Dependencies: `ultralytics`, `jtop` (jetson-stats), `rclpy` (ROS 2 Jazzy).

How to Use / Execution
----------------------
* `convert_engines.py` and `benchmark_jetson.py` are executed standalone via Python3 for model preparation and testing.
* `vision_node.py` is designed to be launched as a background subprocess by the main System Controller UI, or manually via standard ROS 2 execution.

Dependencies & Interactions
---------------------------
* Ingests `.onnx` models from the Training module.
* Interacts directly with the `Software` directory by publishing JSON detection payloads to `/seezy/detections` and raw annotated image bytes to `/seezy/camera/annotated`.
# SEEZY Robot - Mapping Package

## Overview
This package handles the Simultaneous Localization and Mapping (SLAM) capabilities for the SEEZY robot. It uses `slam_toolbox` to process LiDAR scans and odometry, creating a 2D occupancy grid map of unknown environments in real-time while keeping track of the robot's location.

---

## 🛠️ Configuration and Tuning Guide

If you need to improve map quality, adjust to a physical hardware change, or fix mapping errors (like "double walls"), here is where you make those manual changes:

* **Adjusting LiDAR Range (`config/slam_toolbox.yaml`):** Update the `max_laser_range` (currently set to `12.0`). This must perfectly match the maximum physical or simulated range of your LiDAR so the algorithm doesn't process phantom points.
* **Map Resolution (`config/slam_toolbox.yaml`):** The `resolution` parameter determines map detail (default is `0.05` meters per pixel). Lowering this (e.g., to `0.02`) creates sharper, more detailed maps but requires significantly more CPU power and RAM.
* **Fixing Map Drift / Double Walls (`config/slam_toolbox.yaml`):** Ensure `do_loop_closing` is set to `true`. If the map starts tearing or duplicating walls when the robot revisits an area, you can tweak `loop_search_maximum_distance` to help it recognize previously mapped areas better.
* **Map Saver Thresholds (`launch/slam.launch.py`):** Under the `nav2_map_saver` node, you can adjust `"free_thresh_default"` and `"occupied_thresh_default"`. Change these if you find the saved map interprets obstacles too aggressively or too loosely.
# SEEZY Robot - Description Package

## Overview
This package contains the physical and visual descriptions of the SEEZY robot. It includes the URDF/Xacro models, 3D meshes (STL files), Gazebo simulation physics configurations, and the simulated world environments.

---

## 🛠️ Configuration and Tuning Guide

If you need to change how the robot looks, behaves in the simulation, or the environment it drives in, here is where you make those manual changes:

* **Simulation World**
  * *File:* `launch/gazebo.launch.py`
  * *What to change:* Change the `world` default argument to load a different `.sdf` file (e.g., from `supermarket_world.sdf` to `empty.world`).

* **Robot Weight & Inertia**
  * *File:* `urdf/robot.urdf.xacro`
  * *What to change:* Update the `<mass value="8.0"/>` and inertia (`ixx`, `iyy`, `izz`) values inside the `<inertial>` tags if the physical robot gets heavier or lighter.

* **Wheel Friction (Physics)**
  * *File:* `urdf/robot_gazebo.xacro`
  * *What to change:* Adjust `<mu1>` and `<mu2>` values for the left and right wheels. If the robot jitters or shakes in the Gazebo simulation, lower these extreme values (e.g., to 100.0 or 200.0).

* **LiDAR Sensor Properties**
  * *File:* `urdf/robot_gazebo.xacro`
  * *What to change:* Change the `<range>` (min/max distance) and `<samples>` inside the `<sensor name="lidar">` plugin block to simulate different LiDAR models or ranges.
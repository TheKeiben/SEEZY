# SEEZY Robot - Bringup Package

## Overview
This package is the main orchestration unit for the SEEZY robot's simulation environment. It contains the essential ROS 2 launch files required to bring up the robot in Gazebo, start the hardware controllers, and initialize either the mapping (SLAM) or autonomous navigation (Nav2) stacks.

## Package Contents

* **`launch/seezy_test_sim_slam.py`**
  The SLAM (Simultaneous Localization and Mapping) bringup file. It sequentially launches the Gazebo simulation, hardware controllers, and the SLAM Toolbox, allowing the user to teleoperate the robot and generate a new map of the environment.

* **`launch/seezy_test_sim.py`**
  The full autonomous navigation bringup file. It launches the simulation environment, waits for it to fully load, spawns the controllers and RViz2, and finally initializes Localization (AMCL) and Navigation (Nav2) using structured timer delays for a stable and safe startup.

* **`CMakeLists.txt` & `package.xml`**
  Standard ROS 2 package configuration files defining the build instructions, installation rules for the launch directories, and execution dependencies (e.g., `controller`, `description`, `mapping`, `localization`).

## Usage Instructions

Make sure you have built your workspace and sourced the setup file before running these commands:

```bash
# Navigate to your workspace
cd /<your_path>/SEEZY_FINAL/simulation_robot
colcon build --packages-select bringup
source install/setup.bash




 <?xml version="1.0"?>
<package format="3">
  <!-- ========================================== -->
  <!-- 1. Package Identification                  -->
  <!-- ========================================== -->
  <name>controller</name>
  <version>0.0.0</version>
  <description>The controller package</description>
  <maintainer email="SEEZY@gmail.com">YovelBenHamo</maintainer>
  <license>Apache 2.0</license>
  <author email="SEEZY@gmail.com">YovelBenHamo</author>

  <!-- ========================================== -->
  <!-- 2. Build Tool Dependencies                 -->
  <!-- ========================================== -->
  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>ament_cmake_python</buildtool_depend>


  <depend>rclcpp</depend>
  <depend>rclpy</depend>
  <depend>geometry_msgs</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>nav_msgs</depend>
  <depend>tf2_ros</depend>
  <depend>tf2</depend>
  <depend>eigen</depend>
  
  <!-- ========================================== -->
  <!-- 3. Execution Dependencies                  -->
  <!-- ========================================== -->
  <!-- Python and Messages (Used at runtime if python nodes exist) -->
  <exec_depend>tf_transformations</exec_depend>
  <exec_depend>ros2launch</exec_depend>
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>xacro</exec_depend>
  <exec_depend>controller_manager</exec_depend>
  <exec_depend>ros2_controllers</exec_depend>
  <exec_depend>ros2_control</exec_depend>
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>

</package> 
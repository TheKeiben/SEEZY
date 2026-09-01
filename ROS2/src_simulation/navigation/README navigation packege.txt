# SEEZY Robot - Navigation Package

## Overview
This package is the "brain" of the SEEZY robot. It utilizes the ROS 2 Nav2 stack to handle global path planning, local obstacle avoidance, and complex recovery behaviors. It relies on a custom Behavior Tree (BT) to make smart decisions when the robot is stuck or navigating dynamically changing environments.

---

## 🛠️ Configuration and Tuning Guide

If the robot is driving too fast, hitting obstacles, or failing to reach its goal, here is where you make adjustments:

* **Adjusting Robot Speed and Acceleration**
  * *File:* `config/nav2_params.yaml` (under `FollowPath` controller)
  * *What to change:* Modify `desired_linear_vel` (default `0.30`) to make the robot drive faster or slower. Adjust `max_linear_accel` and `max_angular_accel` for smoother starts and stops.

* **Obstacle Clearance (Inflation Radius)**
  * *File:* `config/nav2_params.yaml` (under `local_costmap` and `global_costmap`)
  * *What to change:* Tweak the `inflation_radius` (default `0.5`). Increase this value if the robot drives dangerously close to walls, or decrease it if the robot refuses to pass through narrow doorways.

* **Robot Physical Size (Footprint)**
  * *File:* `config/nav2_params.yaml` (under `local_costmap` and `global_costmap`)
  * *What to change:* Ensure the `footprint` array strictly matches the physical dimensions of the SEEZY robot. This tells the algorithm exactly how much space the robot occupies.

* **Goal Precision Tolerance**
  * *File:* `config/nav2_params.yaml` (under `general_goal_checker`)
  * *What to change:* Adjust `xy_goal_tolerance` (default `0.10` meters) and `yaw_goal_tolerance`. If the robot dances around the goal and struggles to finish the task, slightly increase these numbers to make it less strict.

* **Recovery Logic and Behavior Trees**
  * *File:* `config/navigate_to_pose_w_replanning_and_recovery.xml`
  * *What to change:* This XML file dictates what the robot does when it gets stuck. You can edit the parameters here (like `wait_duration="5.0"` or the `Spin` behavior) to change how the robot attempts to free itself before giving up.
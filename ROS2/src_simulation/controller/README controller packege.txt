## SEEZY Robot - Controller Package

### Overview & Contents
This package manages the hardware interfaces and kinematic controllers for the SEEZY robot. It uses `ros2_control` to translate velocity commands into specific wheel movements.

* **`config/controller.yaml`**: The main configuration file for physical dimensions and speed limits.
* **`launch/controller.launch.py`**: The launch file responsible for spawning the controllers.
* **`CMakeLists.txt` & `package.xml`**: Build definitions and system dependencies.

### Usage Instructions
This package is typically launched automatically. To test the controllers independently, run:
> `ros2 launch controller controller.launch.py use_sim_time:=true`

---

### 🛠️ Configuration and Tuning Guide
To change the robot's size, speed, or acceleration, edit the values inside **`config/controllers.yaml`**:

* **`wheel_separation`**: The distance between the center of the left and right wheels (meters).
* **`wheel_radius`**: The radius of the driving wheels (meters).
* **`linear.x.max_velocity` / `min_velocity`**: Maximum forward and backward speed (m/s).
* **`linear.x.max_acceleration`**: Acceleration rate. Lower values mean smoother, slower starts.
* **`angular.z.max_velocity`**: Maximum turning speed (rad/s).
* **`angular.z.max_acceleration`**: How aggressively the robot begins a turn.
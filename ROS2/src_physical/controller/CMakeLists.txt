cmake_minimum_required(VERSION 3.8)
project(controller)

# ==========================================
# 1. Find Dependencies
# ==========================================
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2 REQUIRED)
find_package(Eigen3 REQUIRED)

include_directories(${EIGEN3_INCLUDE_DIR})

# ==========================================
# 2. Build the C++ Nodes
# ==========================================
add_executable(esp32_odometry src/esp32_odometry.cpp)
ament_target_dependencies(esp32_odometry rclcpp geometry_msgs std_msgs nav_msgs tf2 tf2_ros)

# ==========================================
# 3. Install Rules (Copying files to the workspace)
# ==========================================
# Install the executable C++ nodes
install(TARGETS 
  esp32_odometry
  DESTINATION lib/${PROJECT_NAME}
)

# Install the launch and config directories
install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# Install the Python module! (Because of the __init__.py folder)
ament_python_install_package(${PROJECT_NAME})

# ==========================================
# 4. Package Export
# ==========================================
ament_package()
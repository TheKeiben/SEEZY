# ==========================================
# 1. Basic CMake Configuration
# ==========================================
cmake_minimum_required(VERSION 3.8)
project(controller)

# ==========================================
# 2. Build Dependencies
# ==========================================
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
#find_package(rclcpp REQUIRED)
#find_package(geometry_msgs REQUIRED)
#find_package(std_msgs REQUIRED)
#find_package(sensor_msgs REQUIRED)
#find_package(nav_msgs REQUIRED)
#find_package(tf2_ros REQUIRED)
#find_package(tf2 REQUIRED)
#find_package(Eigen3 REQUIRED)

include_directories(${EIGEN3_INCLUDE_DIR})

# ==========================================
# 3. Install Python Modules
# ==========================================
# Installs the python package (the 'controller' directory containing __init__.py)
ament_python_install_package(${PROJECT_NAME})

# ==========================================
# 4. Install Directories (Launch & Config)
# ==========================================
# Ensures the config files and launch files are copied to the install space
install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# ==========================================
# 5. Package Initialization
# ==========================================
ament_package()
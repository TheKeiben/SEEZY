# ==========================================
# 1. Basic CMake Configuration
# ==========================================
cmake_minimum_required(VERSION 3.8)
project(localization)

# ==========================================
# 2. Build Dependencies
# ==========================================
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# ==========================================
# 3. Python Modules
# ==========================================
# Installs Python nodes/modules if they exist in the package
ament_python_install_package(${PROJECT_NAME})

# ==========================================
# 4. Install Directories
# ==========================================
# Copies launch files, configurations, and RViz settings to the install space
install(
  DIRECTORY launch config 
  DESTINATION share/${PROJECT_NAME}
)

# ==========================================
# 5. Package Initialization
# ==========================================
ament_package()

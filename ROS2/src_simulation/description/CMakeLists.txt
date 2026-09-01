# ==========================================
# 1. Basic CMake Configuration
# ==========================================
cmake_minimum_required(VERSION 3.8)
project(description)

# ==========================================
# 2. Build Dependencies
# ==========================================
find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)

# ==========================================
# 3. Install Directories
# ==========================================
# Copies all the simulation and description files (meshes, URDF, worlds, etc.) 
# to the install space so they can be found by ROS 2 at runtime.
install(
  DIRECTORY launch meshes urdf rviz worlds
  DESTINATION share/${PROJECT_NAME}
)
# ==========================================
# 4. Testing
# ==========================================
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# ==========================================
# 5. Package Initialization
# ==========================================
ament_package()
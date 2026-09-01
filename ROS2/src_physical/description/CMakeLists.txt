cmake_minimum_required(VERSION 3.5)
project(description)

# ==========================================
# 1. Find Dependencies
# ==========================================
find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)

# ==========================================
# 2. Install Rules (Copying files to the workspace)
# ==========================================
install(
  DIRECTORY launch meshes urdf rviz
  DESTINATION share/${PROJECT_NAME}
)

# ==========================================
# 3. Testing Dependencies
# ==========================================
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# ==========================================
# 4. Package Export
# ==========================================
ament_package()
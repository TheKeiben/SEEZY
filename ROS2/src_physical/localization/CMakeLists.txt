cmake_minimum_required(VERSION 3.8)
project(localization)

# ==========================================
# 1. Compiler Options
# ==========================================
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ==========================================
# 2. Find Dependencies
# ==========================================
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# ==========================================
# 3. Install Rules
# ==========================================
# Install the Python module
ament_python_install_package(${PROJECT_NAME})


install(
  DIRECTORY launch config 
  DESTINATION share/${PROJECT_NAME}
)

# ==========================================
# 4. Package Export
# ==========================================
ament_package()

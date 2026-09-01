# ==========================================
# 1. Basic CMake Configuration
# ==========================================
# Set the minimum required version of CMake
cmake_minimum_required(VERSION 3.8)

# Define the name of the project/package
project(bringup)

# ==========================================
# 2. Compiler Options
# ==========================================
# Add standard compiler warnings for C++ if using GCC or Clang
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ==========================================
# 3. Dependencies
# ==========================================
# Find the necessary ament build system package
find_package(ament_cmake REQUIRED)

# ==========================================
# 4. Install Rules
# ==========================================
# Install the 'launch' directory to the package's share destination.
# This ensures that 'ros2 launch' can find and execute these files.
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# ==========================================
# 5. Package Initialization
# ==========================================
# Required macro to properly configure the ament package
ament_package()
================================================================================
ESP32 Firmware Module README
================================================================================

Directory Overview
------------------
This directory houses the custom C++ firmware for the ESP32 microcontroller, acting as the low-level hardware bridge for the SEEZY robotic platform. It is responsible for reading ultra-fast encoder hardware interrupts, executing a closed-loop 50Hz hardware PID motor control cycle, and maintaining a highly resilient micro-ROS connection with the main Jetson Orin Nano processor.

File Overview
-------------
* main.cpp: The master firmware file. It contains all physical GPIO pin definitions, hardware interrupt service routines (ISRs), motor PWM control logic, PID calculations, and the micro-ROS node entity management. 

Setup & Installation
--------------------
* This codebase must be compiled and flashed using the PlatformIO IDE extension in VS Code. It is structured with strict C++ function prototypes and `<Arduino.h>` inclusions, meaning it will not compile out-of-the-box in the standard Arduino IDE.
* The `micro_ros_arduino` library must be included as a dependency in your `platformio.ini` environment block.
* When flashing the firmware via USB, you must physically press and hold the "BOOT" button on the ESP32 board during the terminal's "Connecting..." phase to allow the upload to begin.

How to Use / Execution
----------------------
* The firmware executes automatically the moment the ESP32 receives power.
* It operates on a headless Ping State Machine (`rmw_uros_ping_agent`). It will passively ping the serial port waiting for the Jetson's `micro_ros_agent` to launch. 
* Once the software UI starts the ROS 2 process, the ESP32 automatically creates its ROS entities and begins active motor control. If the UI stops the ROS 2 process, the ESP32 zeroes the motors, destroys the memory entities, and safely returns to a waiting state without requiring a manual reset.

Dependencies & Interactions
---------------------------
* Subscribes to: `/cmd_vel` (Receives target linear and angular velocities from the Nav2 stack or manual UI controls).
* Publishes to: `/encoder/left` and `/encoder/right` (Raw tick data for odometry calculation), as well as `/debug/left` and `/debug/right` (Target vs. Actual speeds for live PID tuning).
* Services: Hosts the `/seezy/reset_esp` Trigger service, enabling the main Python system controller to remotely force a hard reboot of the microcontroller if hardware faults occur.
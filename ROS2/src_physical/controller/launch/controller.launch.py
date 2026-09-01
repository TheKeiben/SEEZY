import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    # ==========================================
    # 1. Define the Time Variable
    # ==========================================
    # Argument to toggle between simulation and physical robot
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Set to true if running Gazebo simulation"
    )
    
    use_sim_time = LaunchConfiguration("use_sim_time")
    # ==========================================
    # 2. PHYSICAL ROBOT (Runs ONLY when use_sim_time is False)
    # ==========================================
    esp32_odometry_node = Node(
        package="controller",
        executable="esp32_odometry",
        name="esp32_odometry",
        parameters=[
            {"wheel_radius": 0.0975},
            {"wheel_separation": 0.33},
            {"ticks_per_rev": 38300.0}
        ],
        condition=UnlessCondition(use_sim_time)
    )

    # ==========================================
    # 3. Return all Commands to the System
    # ==========================================
    return LaunchDescription(
        [
            use_sim_time_arg,
            esp32_odometry_node,
        ]
    )
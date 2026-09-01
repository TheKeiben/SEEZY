import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    """
    Controller launch file.
    Spawns the joint state broadcaster and the differential drive controller.
    Uses 'use_sim_time' to conditionally launch nodes for simulation only.
    """

    # ==========================================
    # 1. Define Launch Arguments
    # ==========================================
    # Argument to toggle between simulation and physical robot
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Set to true if running Gazebo simulation"
    )
    
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Spawns the joint_state_broadcaster to publish wheel states
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        condition=IfCondition(use_sim_time)
    )
    # Spawns the main differential drive controller
    wheel_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "controller", 
            "--controller-manager", 
            "/controller_manager"
        ],
        condition=IfCondition(use_sim_time)
    )

    # ==========================================
    # 3. Return Launch Description
    # ==========================================
    return LaunchDescription(
        [
            use_sim_time_arg,
            joint_state_broadcaster_spawner,
            wheel_controller_spawner,
        ]
    )
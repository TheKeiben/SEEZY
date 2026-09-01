import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # ==========================================================
    # 1. Get the path to the 'description' package directory
    # ==========================================================
    description_dir = get_package_share_directory("description")

    # ==========================================================
    # 2. Declare Launch Arguments
    # ==========================================================
    
    # CRITICAL: Accept 'use_sim_time' from the master bringup file
    use_sim_time_arg = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true"
    )
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Declare the path to the URDF/Xacro model
    model_arg = DeclareLaunchArgument(
        name="model", 
        default_value=os.path.join(description_dir, "urdf", "robot.urdf.xacro"),
        description="Absolute path to robot urdf file"
    )

    # ==========================================================
    # 3. Parse the Robot Description (URDF)
    # ==========================================================
    robot_description = ParameterValue(
        Command(["xacro ", LaunchConfiguration("model")]),
        value_type=str
    )

    # ==========================================================
    # 4. Robot State Publisher Node
    # Publishes the kinematic tree (TF) of the robot.
    # ==========================================================
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{
            "robot_description": robot_description,
            "use_sim_time": use_sim_time
        }]
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(get_package_share_directory("description"), "rviz", "yovel_test_18_08.rviz")],
        parameters=[{"use_sim_time": use_sim_time}]
    )


    # ==========================================================
    # Return all nodes to the launch system
    # ==========================================================
    return LaunchDescription([
        use_sim_time_arg,
        model_arg,
        robot_state_publisher_node,
        rviz_node
    ])
import os
from os import pathsep
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    """
    Launch file for the description package.
    Loads the robot's URDF/Xacro, starts the robot_state_publisher,
    and spawns the robot into the new Gazebo (Ignition) environment.
    """
    description = get_package_share_directory("description")

    # ==========================================
    # 1. Launch Arguments
    # ==========================================
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock if true"
    )
    use_sim_time = LaunchConfiguration("use_sim_time")

    model_arg = DeclareLaunchArgument(
        name="model", default_value=os.path.join(
                description, "urdf", "robot.urdf.xacro"
            ),
        description="Absolute path to robot urdf file"
    )

    world_arg = DeclareLaunchArgument(
        name="world", 
        default_value="supermarket_world.sdf",
        description="World file name including extension (e.g. supermarket_world.sdf)"
    )

    # ==========================================
    # 2. Path Configurations & Environment Variables
    # ==========================================
    world_path = PathJoinSubstitution([
            description,
            "worlds",
            LaunchConfiguration("world")
        ]
    )

    # Add the workspace 'share' directory to the Gazebo resource path 
    # so it can find the meshes via package:// URIs
    model_path = str(Path(description).parent.resolve())
    model_path += pathsep + os.path.join(get_package_share_directory("description"), 'models')

    gazebo_resource_path = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        model_path
        )

    # ==========================================
    # 3. Robot Description (Xacro processing)
    # ==========================================

    ros_distro = os.environ["ROS_DISTRO"]
    is_ignition = "True" if ros_distro == "humble" else "False"

    robot_description = ParameterValue(Command([
            "xacro ",
            LaunchConfiguration("model"),
            " is_ignition:=",
            is_ignition
        ]),
        value_type=str
    )

    # ==========================================
    # 4. Nodes and Gazebo Includes
    # ==========================================

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description,
                     "use_sim_time": use_sim_time}]
    )

    # Launch Gazebo Simulator
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory("ros_gz_sim"), "launch"), "/gz_sim.launch.py"]),
                launch_arguments={
                    "gz_args": PythonExpression(["'", world_path, " -v 4 -r'"])
                }.items()
             )

    # Spawn the robot entity inside Gazebo
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-topic", "robot_description",
                   "-name", "robot"],
    )

    # Bridge ROS 2 topics with Gazebo topics (Clock and LiDAR/Scan)
    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan"
        ]
    )

    # ==========================================
    # 5. Return Launch Description
    # ==========================================
    return LaunchDescription([
        use_sim_time_arg,
        model_arg,
        world_arg, 
        gazebo_resource_path,
        robot_state_publisher_node,
        gazebo,
        gz_spawn_entity,
        gz_ros2_bridge
    ])
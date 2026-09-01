import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    """
    Launch file to bring up the robot in simulation (Gazebo), 
    start the controllers, and launch SLAM mapping.
    """

    # ==========================================
    # 1. Define Launch Arguments and Configurations
    # ==========================================
    # Set 'use_sim_time' to true by default for simulation environments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ==========================================
    # 2. Define Paths to Included Launch Files
    # ==========================================
    
    # Gazebo Simulator: Loads the virtual environment and the robot description
    gazebo_launch_path = os.path.join(
        get_package_share_directory('description'),
        'launch',
        'gazebo.launch.py' 
    )

    # Controller: Spawns virtual controllers in Gazebo
    controller_launch_path = os.path.join(
        get_package_share_directory('controller'),
        'launch',
        'controller.launch.py'
    )

    # Mapping: Launches SLAM Toolbox to create a map of the virtual environment
    mapping_launch_path = os.path.join(
        get_package_share_directory('mapping'),
        'launch',
        'slam.launch.py'
    )

    # ==========================================
    # 3. Create Launch Actions
    # ==========================================

    # Include Gazebo launch description
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # Include Controller launch description
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(controller_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # Include Mapping (SLAM) launch description
    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mapping_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # ==========================================
    # 4. Return Launch Description
    # ==========================================
    # Return all commands to the ROS 2 launch system to execute them together
    return LaunchDescription([
        use_sim_time_arg,
        gazebo_launch,
        controller_launch,
        mapping_launch
    ])
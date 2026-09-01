import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # ==========================================
    # 1. Define the Time Variable
    # ==========================================
    # False for physical robot by default, True for simulation
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    use_sim_time = LaunchConfiguration('use_sim_time')

   # ==========================================
    # 2. Paths to the Launch Files
    # ==========================================
    
    # Robot description and RViz
    description_launch_path = os.path.join(
        get_package_share_directory('description'),
        'launch',
        'display.launch.py' 
    )

    # Controllers, Odometry from ESP32
    controller_launch_path = os.path.join(
        get_package_share_directory('controller'),
        'launch',
        'controller.launch.py'
    )

    # Mapping - SLAM Toolbox to create a new map
    mapping_launch_path = os.path.join(
        get_package_share_directory('mapping'),
        'launch',
        'slam.launch.py'
    )

    # ==========================================
    # 3. Create the launch commands passing the use_sim_time variable
    # ==========================================

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(description_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(controller_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mapping_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # ==========================================
    # 4. Return all Commands to the System
    # ==========================================
    return LaunchDescription([
        use_sim_time_arg,
        description_launch,
        controller_launch,
        mapping_launch,
    ])
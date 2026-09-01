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
        description='Use simulation clock if true'
    )
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ==========================================
    # 2. Paths to the launch files of the different packages
    # ==========================================
    
    # Robot description and RViz (loads your saved map as configured in display.launch.py)
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

    # Localization - Global positioning on the map (AMCL)
    localization_launch_path = os.path.join(
        get_package_share_directory('localization'),
        'launch',
        'localization.launch.py'
    )

    # Navigation - Nav2 (including Costmaps and Path Planning)
    navigation_launch_path = os.path.join(
        get_package_share_directory('navigation'),
        'launch',
        'navigation.launch.py'
    )

    # ==========================================
    # 3. Create the launch commands passing the use_sim_time variable to all
    # ==========================================

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(description_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(controller_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(localization_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(navigation_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    # ==========================================
    # 4. Return all commands to the system to run together
    # ==========================================
    return LaunchDescription([
        use_sim_time_arg,
        description_launch,
        controller_launch,
        localization_launch,
        navigation_launch,
    ])
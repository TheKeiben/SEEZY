import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter
from launch.actions import TimerAction

def generate_launch_description():
    """
    Full simulation bringup file:
    Launches Gazebo, waits, then launches controllers and RViz, 
    and finally launches Localization (AMCL) and Navigation (Nav2).
    """

    # ==========================================
    # 1. Define Launch Arguments and Configurations
    # ==========================================
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ==========================================
    # 2. Define Paths to Included Launch Files
    # ==========================================
    
    # Gazebo Simulator
    gazebo_launch_path = os.path.join(
        get_package_share_directory('description'),
        'launch',
        'gazebo.launch.py' 
    )


    # Controllers (Spawns the virtual controllers in Gazebo)
    controller_launch_path = os.path.join(
        get_package_share_directory('controller'),
        'launch',
        'controller.launch.py'
    )

    # Localization (AMCL)
    localization_launch_path = os.path.join(
        get_package_share_directory('localization'),
        'launch',
        'localization.launch.py'
    )

    # Navigation (Nav2)
    navigation_launch_path = os.path.join(
        get_package_share_directory('navigation'),
        'launch',
        'navigation.launch.py'
    )

    # ==========================================
    # 3. Create Launch Actions
    # ==========================================

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_path),
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

    # RViz2 Node configuration
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(get_package_share_directory("description"), "rviz", "yovel_test_18_08.rviz")],
        parameters=[{"use_sim_time": use_sim_time}]
    )

    # ==========================================
    # 4. Timer Actions for Sequential Bringup
    # ==========================================

    # Delay controllers and RViz to allow Gazebo to fully load
    delayed_rviz = TimerAction(
        period=15.0, # Wait 15 seconds before launching these nodes
        actions=[
            controller_launch,
            rviz_node
        ]
    )

    # Delay Nav2 and Localization to allow controllers to initialize completely
    delayed_controller = TimerAction(
        period=40.0, # Wait 40 seconds before launching these nodes
        actions=[
            localization_launch,
            navigation_launch,
        ]
    )

    # ==========================================
    # 5. Return Launch Description
    # ==========================================
    return LaunchDescription([
        use_sim_time_arg,
        gazebo_launch,
        delayed_rviz,
        delayed_controller
    ])
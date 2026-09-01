import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    # ==========================================
    # 1. Launch Configurations & Environment
    # ==========================================
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    # ==========================================
    # 2. Declare Launch Arguments
    # ==========================================
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )

    # ==========================================
    # 3. Path Substitutions
    # ==========================================
    nav2_pkg = get_package_share_directory('navigation')
    params_file = os.path.join(nav2_pkg, 'config', 'nav2_params.yaml')

    # DYNAMIC XML PATH: Finds the BT XML file dynamically regardless of the computer/robot
    bt_xml_file = os.path.join(nav2_pkg, 'config', 'navigate_to_pose_w_replanning_and_recovery.xml')

    # ==========================================
    # 4. Nodes Declaration
    # ==========================================
    nav2_planner = Node(
        package='nav2_planner', 
        executable='planner_server', 
        name='planner_server',
        output='screen', 
        parameters=[params_file, {'use_sim_time': use_sim_time}]
    )

    nav2_controller = Node(
        package='nav2_controller', 
        executable='controller_server', 
        name='controller_server',
        output='screen', 
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel', '/cmd_vel')]
    )

    nav2_behaviors = Node(
        package='nav2_behaviors', 
        executable='behavior_server', 
        name='behavior_server',
        output='screen', 
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel', '/cmd_vel')]
    )

    nav2_bt_navigator = Node(
        package='nav2_bt_navigator', 
        executable='bt_navigator', 
        name='bt_navigator',
        output='screen', 
        parameters=[
            params_file, 
            {
                'use_sim_time': use_sim_time,
                'default_nav_to_pose_bt_xml': bt_xml_file # Overrides the YAML file with the exact path!
            }
        ]
    )    

    nav2_lifecycle_manager = Node(
        package='nav2_lifecycle_manager', 
        executable='lifecycle_manager', 
        name='lifecycle_manager_navigation',
        output='screen', 
        parameters=[{
            'use_sim_time': use_sim_time, 
            'autostart': True,
            'node_names': ['planner_server', 'controller_server', 'behavior_server', 'bt_navigator']
        }]
    )    

    # ==========================================
    # 5. Return Launch Description
    # ==========================================
    return LaunchDescription([
        use_sim_time_arg,
        nav2_planner,
        nav2_controller,
        nav2_behaviors,
        nav2_bt_navigator,
        nav2_lifecycle_manager
    ])

    

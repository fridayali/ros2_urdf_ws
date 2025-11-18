from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def launch_setup(context, *args, **kwargs):
    # Map Server node
    map_server = Node(
        package='my_robot_bringup',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    # EKF node
    ekf_node = Node(
        package='my_robot_bringup',
        executable='amiga_ekf',
        name='amiga_ekf',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    # Nav2 launch
    nav2_node = Node(
        package='my_robot_bringup',
        executable='amiga_navitation',
        name='amiga_navitation',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    # RViz node
    rviz_node = Node(
        package='nav2_bringup',
        executable='rviz_launch',
        name='rviz_launch',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    # Lifecycle set for map_server
    lifecycle_map_server_configure = Node(
        package='rclpy',
        executable='lifecycle_manager',
        name='lifecycle_manager_map_server',
        arguments=['--set', '/map_server', 'configure'],
        output='screen',
    )

    lifecycle_map_server_activate = Node(
        package='rclpy',
        executable='lifecycle_manager',
        name='lifecycle_manager_map_server',
        arguments=['--set', '/map_server', 'activate'],
        output='screen',
    )

    return [map_server, ekf_node, nav2_node, rviz_node, lifecycle_map_server_configure, lifecycle_map_server_activate]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='False', description='Use simulation time'),
        OpaqueFunction(function=launch_setup)
    ])

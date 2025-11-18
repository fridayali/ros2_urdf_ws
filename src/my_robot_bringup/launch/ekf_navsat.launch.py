from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('my_robot_bringup')
    config_file = os.path.join(pkg_dir, 'config', 'navsat_ekf.yaml')

    return LaunchDescription([

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_local_node',
            output='screen',
            parameters=[
                config_file,
                {'use_sim_time': True}
            ],
            remappings=[
                ('odometry/filtered', '/odometry/filtered_local')
            ,]
        ),

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_global_node',
            output='screen',
            parameters=[
                config_file,
                {'use_sim_time': True}
            ],
        ),

        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat_transform_node',
            output='screen',
            parameters=[
                config_file,
                {'use_sim_time': True}
            ],
        )
    ])

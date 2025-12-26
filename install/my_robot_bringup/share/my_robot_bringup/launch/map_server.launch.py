from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[
                '/home/cuma_karaaslan/ros2_urdf_ws/src/my_robot_bringup/map/map_param.yaml',
                {'use_sim_time': False}
            ],
        )
    ])

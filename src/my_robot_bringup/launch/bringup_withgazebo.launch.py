from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
import os

def generate_launch_description():

    pkg_my_robot = os.path.join(os.getenv('HOME'), 'ros2_urdf_ws', 'install', 'my_robot_bringup', 'share', 'my_robot_bringup')


    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_my_robot, 'launch', 'my_robot_gazebo.launch.py'))
    )


    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_gps',
        arguments=['0','0','0','0','0','0','gps_link','simple_rover/base_link/navsat']
    )


    map_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_my_robot, 'launch', 'map_server.launch.py'))
    )


    ekf_navsat = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_my_robot, 'launch', 'ekf_navsat.launch.py'))
    )

    # Nav2
    # nav2_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(os.path.join(os.getenv('HOME'), 'ros2_ws', 'install', 'nav2_bringup', 'share', 'nav2_bringup', 'launch', 'navigation_launch.py'))
    # )

    # # RViz
    # rviz_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(os.path.join(os.getenv('HOME'), 'ros2_ws', 'install', 'nav2_bringup', 'share', 'nav2_bringup', 'launch', 'rviz_launch.py'))
    # )

    return LaunchDescription([
        gazebo_launch,
        static_tf,
        map_server,
        ekf_navsat,
        #nav2_launch,
        #rviz_launch
    ])

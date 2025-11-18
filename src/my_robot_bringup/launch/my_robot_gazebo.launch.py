from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import FindExecutable, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_bringup_dir = get_package_share_directory('my_robot_bringup')
    gazebo_config_path = os.path.join(pkg_bringup_dir, 'config', 'gazebo_bridge.yaml')
    
    home_dir = os.path.expanduser('~')
    world_path = os.path.join(
        home_dir, 
        '.gz', 'fuel', 'fuel.gazebosim.org', 
        'cuma_karaaslan', 'models', 'ortho_model', 
        'ortho_world.sdf'
    )

    gz_server = ExecuteProcess(
        cmd=[FindExecutable(name='gz'), 'sim', '-r',  "/home/cuma_karaaslan/ros2_urdf_ws/src/my_robot_bringup/world/test_world.sdf"],
        output='screen'
    )
    
    urdf_path = os.path.join(
        get_package_share_directory('my_robot_description'),
        'urdf',
        'my_robot.urdf.xacro'
    )
    robot_description_content = Command(['xacro', ' ', urdf_path])

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[
                {'robot_description': robot_description_content},
                {'use_sim_time': True}
            ],
        ),
        
        gz_server,
        
        Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            parameters=[
                {'topic': 'robot_description'}, 
                {'x': -43.0},
                {'y': 6.0},
                {'z': 4.0},
                {'yaw': 1.0},
                {'pitch': 1.0},
                {'roll': 2.0},
                {'use_sim_time': True}
            ],
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[
                {'config_file': gazebo_config_path},
                {'use_sim_time': True}
            ],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=['-d', os.path.join(get_package_share_directory('my_robot_description'), 'rviz', 'urdf_config.rviz')],
        ),
         Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='bridge_gz_ros_camera_image',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=['/depth_camera/image'],
            ),
        Node(
                package='ros_gz_image',
                executable='image_bridge',
                name='bridge_gz_ros_camera_depth',
                output='screen',
                parameters=[{'use_sim_time': True}],
                arguments=['/depth_camera/depth_image'],
            )
    ])

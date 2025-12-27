#!/bin/bash


source /opt/ros/humble/setup.bash
source ~/ros2_urdf_ws/install/setup.bash  

echo "Launching Gazebo simulation..."
ros2 launch my_robot_bringup my_robot_gazebo.launch.py &
GAZEBO_PID=$!
sleep 5  

echo "Starting static transform publisher..."
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 gps_link simple_rover/base_link/navsat &
TF_PID=$!
sleep 2

echo "Launching map server..."
ros2 launch my_robot_bringup map_server.launch.py &
MAP_PID=$!
sleep 2

echo "Launching EKF + NavSat..."
ros2 launch my_robot_bringup ekf_navsat.launch.py &
EKF_PID=$!
sleep 2

echo "Launching Nav2 navigation stack..."
ros2 launch nav2_bringup navigation_launch.py &
NAV2_PID=$!
sleep 5

echo "Configuring and activating map_server..."
ros2 lifecycle set /map_server configure
ros2 lifecycle set /map_server activate

echo "Launching RViz..."
ros2 launch nav2_bringup rviz_launch.py &
RVIZ_PID=$!

echo "All nodes started!"
echo "Gazebo PID: $GAZEBO_PID, TF PID: $TF_PID, Map PID: $MAP_PID, EKF PID: $EKF_PID, Nav2 PID: $NAV2_PID, RViz PID: $RVIZ_PID"

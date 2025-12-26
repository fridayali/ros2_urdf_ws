#!/bin/bash

# ROS2 ortamını kaynağa al
source /opt/ros/jazzy/setup.bash
source ~/ros2_urdf_ws/install/setup.bash  # kendi workspace yolunu değiştir

# echo "Launching map server..."
# ros2 launch my_robot_bringup map_server.launch.py &
# MAP_PID=$!
# sleep 2

echo "Launching EKF"
ros2 launch my_robot_bringup amiga_navsat_ekf.launch.py &
EKF_PID=$!
sleep 2

echo "Launching Robot_description"
ros2 launch my_robot_description display.launch.xml &
EKF_PID=$!
sleep 2

echo "Launching Nav2 navigation stack..."
ros2 launch my_robot_bringup amiga_navigation.launch.py &
NAV2_PID=$!
sleep 5

# echo "Configuring and activating map_server..."
# ros2 lifecycle set /map_server configure
# ros2 lifecycle set /map_server activate

echo "Launching RViz..."
ros2 launch nav2_bringup rviz_launch.py &
RVIZ_PID=$!

echo "All nodes started!"
echo "Map Server PID: $MAP_PID"
echo "EKF PID: $EKF_PID"
echo "Nav2 PID: $NAV2_PID"
echo "RViz PID: $RVIZ_PID"

# CTRL+C (SIGINT) veya SIGTERM alındığında tüm servisleri durdur
trap "echo 'Stopping all services...'; kill $MAP_PID $EKF_PID $NAV2_PID $RVIZ_PID" SIGINT SIGTERM

# Tüm servislerin çalışmasını bekle
wait $MAP_PID $EKF_PID $NAV2_PID $RVIZ_PID

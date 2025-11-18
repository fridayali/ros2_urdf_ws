#!/usr/bin/env python3
"""


#This code will be manage task, it will listen /mission topic and /goal_pose.
#For example, if a goal pose and a mission is sending, when goal pose reached, "1" value will be send on the /hbridhe topic

#Parameters rn: 
"hbridge_duration_sec"= hbridge on/off publish duration


#parameters in the future:
for the different tasks, such as irrigation, measuring the sensor data, spraying etc.


"""
import rclpy
import asyncio
import json
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Int8
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
import math
import time


#the config poses to see 
CONFIG = {
    "points": {
        "home": {"x": 0.0, "y": 0.0, "yaw": 0.0},
        "start": {"x": 5.0, "y": 2.0, "yaw": 0.0},
        "end": {"x": 10.0, "y": 0.0, "yaw": 0.0}
    },
    "hbridge_duration_sec": 5
}

def yaw_to_quaternion(yaw):
    from math import sin, cos
    qz = sin(yaw / 2.0)
    qw = cos(yaw / 2.0)
    return (0.0, 0.0, qz, qw)

class FieldRobotNode(Node):
    def __init__(self):
        super().__init__("field_robot_node")

        # HBridge publisher
        self.hbridge_pub = self.create_publisher(Int8, "hbridge", 10)
        self.get_logger().info("HBridge publisher ready.")

        # Nav2 action client
        self.nav_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

    async def send_hbridge_command(self, value, duration):
        """Send hbridge command for duration seconds"""
        msg = Int8()
        msg.data = value
        end_time = time.time() + duration
        while time.time() < end_time:
            self.hbridge_pub.publish(msg)
            await asyncio.sleep(0.1)  # 10 Hz

    async def send_goal(self, point):
        """Send a goal to Nav2"""
        pose_msg = PoseStamped()
        pose_msg.header.frame_id = "map"
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.pose.position.x = point["x"]
        pose_msg.pose.position.y = point["y"]
        qx, qy, qz, qw = yaw_to_quaternion(point["yaw"])
        pose_msg.pose.orientation.x = qx
        pose_msg.pose.orientation.y = qy
        pose_msg.pose.orientation.z = qz
        pose_msg.pose.orientation.w = qw

        while not self.nav_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Waiting for Nav2 action server...")

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose_msg

        self.get_logger().info(f"Sending goal: x={point['x']} y={point['y']}")
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        goal_handle = await send_goal_future
        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected!")
            return False

        result_future = goal_handle.get_result_async()
        result = await result_future
        self.get_logger().info("Reached goal!")
        return True

async def main_async():
    rclpy.init()
    node = FieldRobotNode()

    try:

        await node.send_goal(CONFIG["points"]["start"])

        await node.send_hbridge_command(1, CONFIG["hbridge_duration_sec"])

        await node.send_goal(CONFIG["points"]["end"])

        await node.send_hbridge_command(-1, CONFIG["hbridge_duration_sec"])

        await node.send_goal(CONFIG["points"]["home"])

        node.get_logger().info("Mission completed!")

    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    asyncio.run(main_async())

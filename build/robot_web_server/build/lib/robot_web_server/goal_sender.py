#!/usr/bin/env python3

"""

this python script listen goal_pose_server topic and it is sending each waypoints 


"""
import rclpy
import math
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import Quaternion
from std_msgs.msg import Float32MultiArray
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus
from pyproj import Transformer


class NavGoalSender(Node):
    
    def __init__(self):
        super().__init__('nav_goal_sender')

        self.ORIGIN_LAT = 39.79610145
        self.ORIGIN_LON = 32.53153553

        try:
            self.transformer = Transformer.from_crs(
                "EPSG:4326",
                "EPSG:32636",
                always_xy=True
            )
            self.origin_x_utm, self.origin_y_utm = self.transformer.transform(
                self.ORIGIN_LON, self.ORIGIN_LAT
            )
            self.get_logger().info(f'Origin of the map: {self.ORIGIN_LAT}, {self.ORIGIN_LON}')
            self.get_logger().info(f'Origin UTM: {self.origin_x_utm:.2f}, {self.origin_y_utm:.2f}')
        except Exception as e:
            self.get_logger().error(f"error: {e}")
            rclpy.shutdown()
            return

        self._action_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        self.web_goal_sub = self.create_subscription(
            Float32MultiArray,
            '/goal_pose_server',
            self.web_goal_callback,
            10
        )
        self.get_logger().info("listening the topic: '/goal_pose_server' ...")

        self.waypoints_queue = []


    def lat_lon_to_xy(self, lat, lon):
        try:
            target_x_utm, target_y_utm = self.transformer.transform(lon, lat)
            goal_x = target_x_utm - self.origin_x_utm
            goal_y = target_y_utm - self.origin_y_utm
            return goal_x, goal_y
        except Exception as e:
            self.get_logger().error(f"GPS tansformin errror (lat: {lat}, lon: {lon}): {e}")
            return None, None

    def euler_to_quaternion(self, yaw_radians):
        q = Quaternion()
        q.z = math.sin(yaw_radians / 2.0)
        q.w = math.cos(yaw_radians / 2.0)
        q.x = 0.0
        q.y = 0.0
        return q

    def parse_waypoints(self, msg):
        data = msg.data
        if len(data) % 3 != 0:
            self.get_logger().warn("Waypoints shouşd be included three parameter (lat, lon, heading).")
            return []

        waypoints = []
        for i in range(0, len(data), 3):
            lat = data[i]
            lon = data[i+1]
            heading = data[i+2]
            waypoints.append((lat, lon, heading))
        return waypoints

    def web_goal_callback(self, msg):
        self.waypoints_queue = self.parse_waypoints(msg)
        if not self.waypoints_queue:
            return
        self.get_logger().info(f"{len(self.waypoints_queue)} waypoints received.")
        self.send_next_waypoint()


    def send_next_waypoint(self):
        if not self.waypoints_queue:
            self.get_logger().info("All waypoints were reeachedd")
            return
        
        lat, lon, heading_degrees = self.waypoints_queue.pop(0)
        goal_x, goal_y = self.lat_lon_to_xy(lat, lon)
        if goal_x is None:
            self.get_logger().error("Waypoint trasnform is not succesfull.")
            self.send_next_waypoint()
            return

        yaw_radians = math.radians(heading_degrees)
        orientation_q = self.euler_to_quaternion(yaw_radians)

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.pose.position.x = goal_x
        goal_msg.pose.pose.position.y = goal_y
        goal_msg.pose.pose.orientation = orientation_q

        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Nav2 Action server error")
            return

        self.get_logger().info(f"Waypoint: X={goal_x:.2f}, Y={goal_y:.2f}, Heading={heading_degrees}°")
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    # --- Action Geri Bildirim ---
    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Remaining distance: {feedback.distance_remaining:.2f} m.')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal refused!')
            # Hatalı waypoint atlanabilir
            self.send_next_waypoint()
            return
        self.get_logger().info('Goal accepted')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Goal reached.')
        else:
            self.get_logger().warn(f'Navigation error: {status}')
        # Bir sonraki waypoint’i gönder
        self.send_next_waypoint()


def main(args=None):
    rclpy.init(args=args)
    node = NavGoalSender()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

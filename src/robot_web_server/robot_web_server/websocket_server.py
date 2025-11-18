#!/usr/bin/env python3

"""

This python script receive command from websocket, such as goal pose, camera request, some config files and missions
and also send current pose, battery, motor temp, tool status etc.
and listen ros2 topics that are gps, rtk/odom, motor_state, battery state, camera1 etc. 





"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import asyncio
import threading
import requests
import websockets
import json
import time
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import NavSatFix, BatteryState,Image
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray, String
import math
import utils
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile
from nav2_msgs.action import NavigateToPose
from tf_transformations import quaternion_from_euler
from cv_bridge import CvBridge
import cv2
import base64
import numpy


#TODO TOOLS EKLENSİN

ROBOT_ID = 6
BASE_URL = "http://backend.agrobrain.com.tr"
REGISTER_URL = f"{BASE_URL}/amiga/register"
ROBOT_PAYLOAD = {
    "robot_id": ROBOT_ID,
    "sensor_states": ["GNSS", "LIDAR", "RGB_CAMERA1", "RGB_CAMERA2","DEPTH_CAMERA","SOIL_SENSOR"]
}
ROBOT_SENSORS = {"sensor_states": ["GNSS", "LIDAR", "RGB_CAMERA1", "RGB_CAMERA2", "DEPTH_CAMERA"]}

from enum import Enum

class CameraState(Enum):
    RGB_CAMERA1_ON = "RGB_CAMERA1_ON"
    RGB_CAMERA1_OFF = "RGB_CAMERA1_OFF"
    RGB_CAMERA1_GET = "RGB_CAMERA1_GET"


class TelemetryListener(Node):
    def __init__(self):
        super().__init__('telemetry_listener')
        self.utils = utils
        self.ws_url = None
        self.config_data = None
        self.telemetry_data = {
            "lat": None,
            "lon": None,
            "heading": None,
            "motor_temps": [None, None, None, None],
            "battery_state": None,
            "tool_status": "STATUS_UNKNOWN",
            "goal_pose_status": 0
        }

        self.camera_data={
            "RGB_CAMERA1":None
        }
        self.cameras_state=CameraState.RGB_CAMERA1_OFF
        self.telemetry_lock = threading.Lock()

        self.create_subscription(NavSatFix, '/gps/fix', self.gps_callback, 10)
        self.create_subscription(Odometry, '/rtk/odom', self.heading_callback, 10)
        self.create_subscription(Float32MultiArray, '/motor_state', self.motor_callback, 10)
        self.create_subscription(BatteryState, '/battery_state', self.battery_callback, 10)
        self.create_subscription(String, '/tool_status', self.tool_callback, 10)
        self.subscription = self.create_subscription(
            Image,
            '/camera1',
            self.image_callback,
            10  
        )
        self.bridge = CvBridge()

        self.mission_pub=self.create_publisher(String,"/mission",10)
        self.goal_pose_pub=self.create_publisher(Float32MultiArray,'/goal_pose_webserver',10)
        self.camera_state_pub=self.create_publisher(String,'/camera_state',10)
        self.goal_state_pub=self.create_publisher(String,'/goal_state',10)
        
      
        self.nav_action_client = ActionClient(self, NavigateToPose, '/navigate_to_goal')

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_async_loop, daemon=True).start()

        asyncio.run_coroutine_threadsafe(self.run(), self.loop)

        self.get_logger().info("Telemetry Listener node initialized")


    def _run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


    def image_callback(self, msg: Image):
            self.camera_data["RGB_CAMERA1"] = None

            if self.cameras_state==CameraState.RGB_CAMERA1_OFF:
                return
            try:

                cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        
                ret, buffer = cv2.imencode('.jpg', cv_image)
                if not ret:
                    self.get_logger().warn("Failed to encode image")
                    return

                jpg_as_text = base64.b64encode(buffer).decode('utf-8')


                camera_data_json = json.dumps(self.camera_data, indent=4)


                with open('/home/cuma_karaaslan/ros2_urdf_ws/src/robot_web_server/robot_web_server/camera_image_base64.txt', 'w') as file:
                    file.write(camera_data_json)
    
                with self.telemetry_lock:
                    self.camera_data["RGB_CAMERA1"] = jpg_as_text
            
            except Exception as e:
                self.get_logger().error(f"Image callback error: {e}")
            
    def gps_callback(self, msg: NavSatFix):
        with self.telemetry_lock:
            self.telemetry_data["lat"] = msg.latitude
            self.telemetry_data["lon"] = msg.longitude

    def heading_callback(self, msg: Odometry):
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y**2 + q.z**2)
        heading = math.degrees(math.atan2(siny_cosp, cosy_cosp))
        with self.telemetry_lock:
            self.telemetry_data["heading"] = heading

    def motor_callback(self, msg: Float32MultiArray):
        with self.telemetry_lock:
            self.telemetry_data["motor_temps"] = list(msg.data[:4])

    def battery_callback(self, msg: BatteryState):
        with self.telemetry_lock:

            self.telemetry_data["battery_state"] = int((float(msg.percentage)-40.0)/(10.0)*100) 

    def tool_callback(self, msg: String):
        with self.telemetry_lock:
            self.telemetry_data["tool_status"] = msg.data



    def send_goal(self, lat, lon, heading, mission_name):

        goal_msg = Float32MultiArray()
        goal_msg.data = [float(lat), float(lon), float(heading)]
        self.goal_pose_pub.publish(goal_msg)


        mission_msg = String()
        mission_msg.data = str(mission_name) 
        self.mission_pub.publish(mission_msg)

        self.get_logger().info(f"Sending: {goal_msg.data}, Mission: {mission_msg.data}")

    def feedback_callback(self, feedback_msg):
        with self.telemetry_lock:
            pass 

    def register_robot(self, retries=5, delay=2):
        for attempt in range(1, retries + 1):
            try:

                response = requests.post(REGISTER_URL, json=ROBOT_PAYLOAD, timeout=5)
                response.raise_for_status()
                self.config_data = response.json()
                self.ws_url = self.config_data.get("websocket_url")
                self.get_logger().info(f"Robot registered. WS URL: {self.ws_url}")
                return self.ws_url
            except requests.exceptions.RequestException as e:
                self.get_logger().warn(f"Attempt {attempt}/{retries} - HTTP register failed: {e}")
                if attempt < retries:
                    time.sleep(delay) 
                else:
                    self.get_logger().error("Max retries reached. Could not register robot.")
                    return None

    async def send_telemetry(self, websocket):
        while True:
            try:
                with self.telemetry_lock:
                    data_to_send_telemetry = self.telemetry_data.copy()
                    data_to_send_camera = self.camera_data.copy()
                await websocket.send(json.dumps(data_to_send_telemetry))
                #await websocket.send(json.dumps(data_to_send_camera))
                if self.cameras_state==CameraState.RGB_CAMERA1_OFF:
                    print("camera_off")
                    pass
                elif self.cameras_state==CameraState.RGB_CAMERA1_GET:
                    print("camera_get")
                    await websocket.send(json.dumps(data_to_send_camera))
                    self.cameras_state=CameraState.RGB_CAMERA1_OFF
                elif self.cameras_state==CameraState.RGB_CAMERA1_ON:
                    print("camera_on")
                    await websocket.send(json.dumps(data_to_send_camera))

                await asyncio.sleep(2)
            except websockets.exceptions.ConnectionClosed:
                self.get_logger().warn("WebSocket closed while sending telemetry")
                break

    async def receive_commands(self, websocket):
        try:
            async for message in websocket:
                self.get_logger().info(f"Command received: {message}")
                data = json.loads(message)

                goal_name = data.get("goal")          
                mission_name = data.get("mission")    
                cameras_state_str = data.get("camera_state") 
                
                zone_id = data.get("zone_id")
                tool_id = data.get("tool_id")

                if cameras_state_str:
                    try:
                        with self.telemetry_lock:
                            self.cameras_state = CameraState(cameras_state_str)
                        self.get_logger().info(f"Camera state updated: {self.cameras_state}")
                    except ValueError:
                        self.get_logger().warn(f"Invalid camra state: {cameras_state_str}")
                        with self.telemetry_lock:
                            self.cameras_state = CameraState.RGB_CAMERA1_OFF 

                target_pose_data = None  

                if self.config_data is None:
                    self.get_logger().error("Config was not found.")
                    continue 

                # -----------------------------------
                # ZONE HEDEFİ
                # -----------------------------------
                if goal_name == "zone":
                    if zone_id is None:
                        self.get_logger().warn("Zone goal was received however id is missing.")
                    else:
                        self.get_logger().info(f"Zone id: {zone_id}")
                        zones = self.config_data.get("zone", [])
                        
                        found = False
                        for zone in zones:
                            if str(zone.get("id")) == str(zone_id):
                                boundary = zone.get("boundary", []) #TODO ilk boundary noktasına gidiliyoe şu an, onun için path_coverage paketini entegre et 
                                if boundary:
                                    first_point = boundary[0]  # firs boundary 
                                    target_pose_data = {
                                        "lat": first_point.get("lat"),
                                        "lon": first_point.get("lon"),
                                        "heading": 0.0
                                    }
                                    self.get_logger().info(
                                        f"Zone: {zone.get('name')} First boundary"
                                    )
                                    found = True
                                else:
                                    self.get_logger().warn(
                                        f"Zone '{zone_id}' but boundary is empty"
                                    )
                                break 

                        if not found:
                            self.get_logger().warn(
                                f"Cannot find zone that has ID:'{zone_id}'."
                            )

                elif goal_name == "tool":
                    if tool_id is None:
                        self.get_logger().warn("Tool goal was received but tool id is null.")
                    else:
                        self.get_logger().info(f"Tool ID = {tool_id}")
                        tools = self.config_data.get("tool", [])
                        found = False

                        for tool in tools:
                            if str(tool.get("id")) == str(tool_id):
                                target_pose_data = tool.get("location")
                                if target_pose_data:
                                    self.get_logger().info(
                                        f"Tool:: {tool.get('name')}."
                                    )
                                    found = True
                                else:
                                    self.get_logger().warn(
                                        f"Tool '{tool_id}' no location data"
                                    )
                                break

                        if not found:
                            self.get_logger().warn(
                                f"No Tool ID: '{tool_id}' in the config."
                            )

                elif goal_name is not None:
                    self.get_logger().info(f"Custom goal:'{goal_name}'")

                    target_pose_data = (
                        self.config_data.get("config", {}).get(goal_name)
                    )

                    if not target_pose_data:
                        self.get_logger().warn(
                            f"No custom goal for: '{goal_name}'."
                        )

                elif goal_name is not None:
                    self.get_logger().warn(f"Unknown goal: {goal_name}")

                if target_pose_data:
                    self.get_logger().info(f"Goal pose: {target_pose_data}")
                else:
                    self.get_logger().warn("No goal")

        except: 
            pass

    async def run(self, reconnect_delay=5):
        while rclpy.ok(): 
            ws_url = self.register_robot() 
            if not ws_url:
                self.get_logger().error(f"Could not get WS URL. Retrying in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay) 
                continue
            try:
                self.get_logger().info(f"Connecting to WS: {ws_url}")
                async with websockets.connect(ws_url) as websocket:
                    await websocket.send(json.dumps(ROBOT_PAYLOAD))
                    print("bağlantı başarılı")
                    send_task = asyncio.create_task(self.send_telemetry(websocket))
                    recv_task = asyncio.create_task(self.receive_commands(websocket))
                    
                    await asyncio.gather(send_task, recv_task)
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                self.get_logger().warn(f"WebSocket disconnected: {e}. Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay) 
            except Exception as e:
                self.get_logger().error(f"Unexpected WebSocket error: {e}")
                await asyncio.sleep(reconnect_delay) 
 


def main():
    rclpy.init()
    node = TelemetryListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Closing...')
    finally:

        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

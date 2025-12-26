import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/cuma_karaaslan/ros2_urdf_ws/install/robot_web_server'

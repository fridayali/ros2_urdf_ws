
#pose message from dict obj
def create_pose_from_dict(loc_dict): 
    from geometry_msgs.msg import PoseStamped
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.pose.position.x = loc_dict["lat"]
    pose.pose.position.y = loc_dict["lon"]
    import tf_transformations
    # q = tf_transformations.quaternion_from_euler(0, 0, loc_dict.get("heading", 0))
    # pose.pose.orientation.x = q[0]
    # pose.pose.orientation.y = q[1]
    # pose.pose.orientation.z = q[2]
    # pose.pose.orientation.w = q[3]
    return pose
#pose message from tuple obj
def create_pose_from_values(lat, lon, heading):
    from geometry_msgs.msg import PoseStamped
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.pose.position.x = lat
    pose.pose.position.y = lon
    import tf_transformations
    q = tf_transformations.quaternion_from_euler(0, 0, heading)
    pose.pose.orientation.x = q[0]
    pose.pose.orientation.y = q[1]
    pose.pose.orientation.z = q[2]
    pose.pose.orientation.w = q[3]
    return pose

#this function return enu coordinates from geodetcic
import numpy as np
a = 6378137.0           #some constants for the lat lon enu transformation  
f = 1/298.257223563      
e2 = 2*f - f**2           

datum_lat = 39.796099
datum_lon = 32.531541

def latlon_to_enu(lat, lon, lat0=datum_lat, lon0=datum_lon):
    
    def geodetic_to_ecef(lat, lon):
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)
        N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
        X = N * np.cos(lat_rad) * np.cos(lon_rad)
        Y = N * np.cos(lat_rad) * np.sin(lon_rad)
        Z = ( (1 - e2) * N ) * np.sin(lat_rad)
        return np.array([X, Y, Z])
    
    X, Y, Z = geodetic_to_ecef(lat, lon)
    X0, Y0, Z0 = geodetic_to_ecef(lat0, lon0)
    
    dX, dY, dZ = X-X0, Y-Y0, Z-Z0 

    lat0_rad = np.radians(lat0)
    lon0_rad = np.radians(lon0)
    
    R = np.array([
        [-np.sin(lon0_rad),             np.cos(lon0_rad),              0],
        [-np.sin(lat0_rad)*np.cos(lon0_rad), -np.sin(lat0_rad)*np.sin(lon0_rad), np.cos(lat0_rad)],
        [np.cos(lat0_rad)*np.cos(lon0_rad),  np.cos(lat0_rad)*np.sin(lon0_rad),  np.sin(lat0_rad)]
    ])
    
    enu = R @ np.array([dX, dY, dZ])
    E, N = enu[0], enu[1]
    return E, N

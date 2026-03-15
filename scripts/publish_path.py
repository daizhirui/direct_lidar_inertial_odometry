#!/usr/bin/env python3

import rospy
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import numpy as np


if __name__ == "__main__":
    # read path from file

    node = rospy.init_node("path_publisher")

    path_file = rospy.get_param("~path_file")
    frame_id = rospy.get_param("~frame_id", "odom")
    path_pub = rospy.Publisher("~path", Path, queue_size=10)

    path_msg = Path()
    path_msg.header.frame_id = frame_id

    data = np.loadtxt(path_file, delimiter=",")
    for i in range(data.shape[0]):
        pose_msg = PoseStamped()
        pose_msg.header.frame_id = frame_id
        pose_msg.pose.position.x = data[i, 0]
        pose_msg.pose.position.y = data[i, 1]
        pose_msg.pose.position.z = data[i, 2]

        pose_msg.pose.orientation.x = data[i, 3]
        pose_msg.pose.orientation.y = data[i, 4]
        pose_msg.pose.orientation.z = data[i, 5]
        pose_msg.pose.orientation.w = data[i, 6]

        path_msg.poses.append(pose_msg)

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        path_pub.publish(path_msg)
        rate.sleep()

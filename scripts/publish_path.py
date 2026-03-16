#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import numpy as np


class PathPublisher(Node):
    def __init__(self):
        super().__init__('path_publisher')

        self.declare_parameter('path_file', '')
        self.declare_parameter('frame_id', 'odom')

        path_file = self.get_parameter('path_file').get_parameter_value().string_value
        frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        if not path_file:
            self.get_logger().error('path_file parameter is required')
            raise SystemExit(1)

        self.path_pub = self.create_publisher(Path, '~/path', 10)

        path_msg = Path()
        path_msg.header.frame_id = frame_id

        data = np.loadtxt(path_file, delimiter=',')
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

        self.path_msg = path_msg
        self.timer = self.create_timer(0.1, self.timer_callback)

    def timer_callback(self):
        self.path_pub.publish(self.path_msg)


def main(args=None):
    rclpy.init(args=args)
    node = PathPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

#
#   Copyright (c)
#
#   The Verifiable & Control-Theoretic Robotics (VECTR) Lab
#   University of California, Los Angeles
#
#   Authors: Kenny J. Chen, Ryan Nemiroff, Brett T. Lopez
#   Contact: {kennyjchen, ryguyn, btlopez}@ucla.edu
#

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, Shutdown
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    current_pkg = FindPackageShare("direct_lidar_inertial_odometry")

    # Launch arguments

    declare_robot_namespace_arg = DeclareLaunchArgument(
        "namespace", default_value="robot", description="Namespace for the robot"
    )
    declare_rviz_arg = DeclareLaunchArgument("rviz", default_value="false", description="Launch RViz")
    declare_pointcloud_topic_arg = DeclareLaunchArgument(
        "pointcloud_topic", default_value="/os_cloud_node/points", description="Pointcloud topic name"
    )
    declare_imu_topic_arg = DeclareLaunchArgument(
        "imu_topic", default_value="/os_cloud_node/imu", description="IMU topic name"
    )
    declare_gt_path_file_arg = DeclareLaunchArgument(
        "gt_path_file",
        default_value="/home/daizhirui/Data/NewerCollege/poses.csv",
        description="Ground truth path file",
    )
    declare_rosbag_dir_arg = DeclareLaunchArgument(
        "rosbag_dir",
        default_value="/home/daizhirui/Data/NewerCollege/2021-07-01-10-37-38-quad-easy.bag.ros2",
        description="Directory for rosbag files",
    )
    declare_rosbag_playrate_arg = DeclareLaunchArgument(
        "rosbag_playrate",
        default_value="0.5",
        description="Play rate for rosbag",
    )
    declare_record_bag_arg = DeclareLaunchArgument(
        "record_bag",
        default_value="false",
        description="Record output topics to a rosbag",
    )
    declare_output_bag_file_arg = DeclareLaunchArgument(
        "output_bag_file",
        default_value="/home/daizhirui/Data/NewerCollege/dlio_newer_college_recording",
        description="Output rosbag file path",
    )

    gt_path_file = LaunchConfiguration("gt_path_file")
    robot_namespace = LaunchConfiguration("namespace")
    rviz = LaunchConfiguration("rviz")
    pointcloud_topic = LaunchConfiguration("pointcloud_topic")
    imu_topic = LaunchConfiguration("imu_topic")
    rosbag_dir = LaunchConfiguration("rosbag_dir")
    rosbag_playrate = LaunchConfiguration("rosbag_playrate")
    record_bag = LaunchConfiguration("record_bag")
    output_bag_file = LaunchConfiguration("output_bag_file")

    # Load parameters
    dlio_yaml_path = PathJoinSubstitution([current_pkg, "cfg", "dlio_newer_college.yaml"])
    dlio_params_yaml_path = PathJoinSubstitution([current_pkg, "cfg", "params.yaml"])

    # Static transform: odom -> robot/odom
    odom_tf_broadcaster = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="odom_tf_broadcaster",
        arguments=[
            "--x",
            "6.825154886605512",
            "--y",
            "-55.33546744126587",
            "--z",
            "0.9433306268722826",
            "--yaw",
            "1.0759642962197828",
            "--pitch",
            "0.06803519183708207",
            "--roll",
            "-0.054227076410519826",
            "--frame-id",
            "odom",
            "--child-frame-id",
            PathJoinSubstitution([robot_namespace, "odom"]),
        ],
    )

    # Static transform: robot/dlio/os_sensor -> os_sensor
    base_link_tf_broadcaster = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_link_tf_broadcaster",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--qw",
            "1",
            "--qx",
            "0",
            "--qy",
            "0",
            "--qz",
            "0",
            "--frame-id",
            PathJoinSubstitution([robot_namespace, "dlio", "lidar"]),
            "--child-frame-id",
            "os_sensor",
        ],
    )

    # Ground truth path publisher
    gt_path_publisher = Node(
        package="direct_lidar_inertial_odometry",
        executable="publish_path.py",
        name="gt_path_publisher",
        output="screen",
        parameters=[
            {"frame_id": "odom"},
            {"path_file": gt_path_file},
        ],
    )

    # DLIO Odometry Node
    dlio_odom_node = Node(
        package="direct_lidar_inertial_odometry",
        executable="dlio_odom_node",
        namespace=robot_namespace,
        output="screen",
        parameters=[
            dlio_yaml_path,
            dlio_params_yaml_path,
            {
                "frames/publishDeskewedInLidarFrame": False,
                "odom/imu/calibration/time": 1.0,
            },
        ],
        remappings=[
            ("pointcloud", pointcloud_topic),
            ("imu", imu_topic),
            ("odom", "dlio/odom_node/odom"),
            ("pose", "dlio/odom_node/pose"),
            ("path", "dlio/odom_node/path"),
            ("kf_pose", "dlio/odom_node/keyframes"),
            ("kf_cloud", "dlio/odom_node/pointcloud/keyframe"),
            ("deskewed", "dlio/odom_node/pointcloud/deskewed"),
        ],
    )

    # DLIO Mapping Node
    dlio_map_node = Node(
        package="direct_lidar_inertial_odometry",
        executable="dlio_map_node",
        namespace=robot_namespace,
        output="screen",
        parameters=[dlio_yaml_path, dlio_params_yaml_path],
        remappings=[
            ("keyframes", "dlio/odom_node/pointcloud/keyframe"),
        ],
    )

    # RViz node
    rviz_config_path = PathJoinSubstitution([current_pkg, "launch", "newer_college.rviz"])
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="dlio_rviz",
        arguments=["-d", rviz_config_path],
        output="screen",
        condition=IfCondition(rviz),
    )

    # Rosbag play node (auto exit all when playback finishes if recording)
    rosbag_play_cmd = [
        "ros2", "bag", "play", rosbag_dir, "--clock", "--rate", rosbag_playrate,
    ]
    rosbag_play_node = ExecuteProcess(
        cmd=rosbag_play_cmd,
        output="screen",
        condition=UnlessCondition(record_bag),
    )
    rosbag_play_node_required = ExecuteProcess(
        cmd=rosbag_play_cmd,
        output="screen",
        on_exit=Shutdown(reason="Rosbag playback finished"),
        condition=IfCondition(record_bag),
    )

    # Rosbag record node
    rosbag_record_node = ExecuteProcess(
        cmd=[
            "ros2",
            "bag",
            "record",
            "-o",
            output_bag_file,
            ["/", robot_namespace, "/dlio/odom_node/odom"],
            ["/", robot_namespace, "/dlio/odom_node/pose"],
            ["/", robot_namespace, "/dlio/odom_node/path"],
            ["/", robot_namespace, "/dlio/odom_node/keyframes"],
            ["/", robot_namespace, "/dlio/odom_node/pointcloud/keyframe"],
            ["/", robot_namespace, "/dlio/odom_node/pointcloud/deskewed"],
            ["/", robot_namespace, "/dlio/map_node/map"],
            "/tf",
            "/tf_static",
        ],
        output="screen",
        condition=IfCondition(record_bag),
    )

    return LaunchDescription(
        [
            declare_robot_namespace_arg,
            declare_rviz_arg,
            declare_gt_path_file_arg,
            declare_rosbag_dir_arg,
            declare_rosbag_playrate_arg,
            declare_record_bag_arg,
            declare_output_bag_file_arg,
            declare_pointcloud_topic_arg,
            declare_imu_topic_arg,
            odom_tf_broadcaster,
            base_link_tf_broadcaster,
            gt_path_publisher,
            dlio_odom_node,
            dlio_map_node,
            rviz_node,
            rosbag_play_node,
            rosbag_play_node_required,
            rosbag_record_node,
        ]
    )

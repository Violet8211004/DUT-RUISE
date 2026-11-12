from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("qr_vision"), "config", "qr.yaml"])

    return LaunchDescription([
        DeclareLaunchArgument("use_camera", default_value="true"),
        Node(
            package="qr_vision",
            executable="camera_node",
            name="camera_node",
            parameters=[params],
            condition=IfCondition(LaunchConfiguration("use_camera")),
        ),
        Node(
            package="qr_vision",
            executable="qr_detector_node",
            name="qr_detector_node",
            parameters=[params],
        ),
        Node(
            package="qr_vision",
            executable="align_node",
            name="align_node",
            parameters=[params],
        ),
    ])

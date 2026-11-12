import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _setup(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)

    actions = [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="laser_tf",
            arguments=[
                value("laser_x"), value("laser_y"), value("laser_z"),
                value("laser_yaw"), "0", "0",
                "base_link", value("laser_frame"),
            ],
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="camera_tf",
            arguments=[
                value("camera_x"), value("camera_y"), value("camera_z"),
                "0", value("camera_pitch"), "0",
                "base_link", "camera_link",
            ],
        ),
        Node(
            package="robot_nav",
            executable="cmd_vel_mux",
            name="cmd_vel_mux",
            parameters=[{"initial_mode": value("control_mode")}],
        ),
    ]

    if value("start_lidar") == "true":
        try:
            share = get_package_share_directory("oradar_lidar")
            actions.append(
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(share, "launch", "ms200_scan.launch.py")
                    )
                )
            )
        except PackageNotFoundError:
            actions.append(LogInfo(msg="未找到 oradar_lidar，未启动雷达驱动"))
    return actions


def generate_launch_description():
    names = [
        ("control_mode", "stop"),
        ("start_lidar", "true"),
        ("laser_frame", "laser"),
        ("laser_x", "0.10"),
        ("laser_y", "0.0"),
        ("laser_z", "0.10"),
        ("laser_yaw", "0.0"),
        ("camera_x", "0.12"),
        ("camera_y", "0.0"),
        ("camera_z", "0.15"),
        ("camera_pitch", "0.0"),
    ]
    arguments = [
        DeclareLaunchArgument(name, default_value=default)
        for name, default in names
    ]
    return LaunchDescription(arguments + [OpaqueFunction(function=_setup)])

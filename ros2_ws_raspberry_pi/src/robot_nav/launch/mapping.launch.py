import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("robot_nav")
    return LaunchDescription([
        DeclareLaunchArgument("use_cmdvel_odom", default_value="false"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(share, "launch", "common.launch.py")),
            launch_arguments={"control_mode": "teleop"}.items(),
        ),
        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam_toolbox",
            output="screen",
            parameters=[os.path.join(share, "config", "slam_mapping.yaml")],
        ),
        Node(
            package="robot_nav",
            executable="cmdvel_odom",
            name="cmdvel_odom",
            condition=IfCondition(LaunchConfiguration("use_cmdvel_odom")),
        ),
    ])

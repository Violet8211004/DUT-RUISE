import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    share = get_package_share_directory("robot_nav")
    nav2_share = get_package_share_directory("nav2_bringup")
    params = os.path.join(share, "config", "nav2_params.yaml")

    return LaunchDescription([
        DeclareLaunchArgument("map", description="建图保存出的 yaml 绝对路径"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(share, "launch", "common.launch.py")),
            launch_arguments={"control_mode": "stop"}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_share, "launch", "bringup_launch.py")),
            launch_arguments={
                "slam": "False",
                "map": LaunchConfiguration("map"),
                "params_file": params,
                "use_sim_time": "False",
                "autostart": "True",
                "use_composition": "False",
            }.items(),
        ),
    ])

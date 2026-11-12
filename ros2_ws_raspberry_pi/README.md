# 树莓派实体小车 ROS 2 工程（Jazzy）

本工作区以你提供的原始 `ros2_ws(1).zip` 为基础：仍包含 `qr_msgs`、`qr_vision`、`robot_nav` 三个包。保留原有树莓派相机、雷达驱动启动方式、SLAM、AMCL、Nav2 MPPI、二维码视觉对位及 `/cmd_vel`（`Twist`）速度切换。此包**已静态检查，但尚未在你的树莓派/实际电机上运行验收**；不要把「可编译」等同于「已完成自主行驶」。

## 1. 实车前置条件（必须先确认）

- 64 位 Ubuntu 24.04 / ROS 2 Jazzy（或使用与你现有系统兼容的环境），树莓派实际摄像头驱动与 LiDAR 驱动正常。
- `/scan` (`sensor_msgs/msg/LaserScan`)、`/odom` (`nav_msgs/msg/Odometry`) 和 TF `odom -> base_link -> laser` 正常，**建图或导航时必须有真实里程计**。原包里的 `cmdvel_odom` 只用于早期诊断，不可代替编码器做实车自主导航。
- **检查底盘真实的速度消息类型**：本工程沿用原实车代码，在 `/cmd_vel` 发布 `geometry_msgs/msg/Twist`；如果电机驱动需要 `TwistStamped`，不能直接运行自动驾驶，必须针对硬件接口另做转换。
- 确保实体急停开关可用、轮子离地时能正常停机，随后才能在空旷场地低速测试。软件停止消息不是硬件急停的替代品。
- **轮廓不要直接照搬仿真**：此前记录的「范围 1.4 × 1.1」未明确单位、原点与是否包含轮子/货架；原先估计的实车车身为约 20 × 15 cm。由于无法据此推出实车完整外廓，本包保留原实车 `robot_radius: 0.20`（两处）作为待测保守配置，不把 1.4 × 1.1 擅自写入实体机器人 footprint；上车前务必实测全车（含轮、支架、载荷）并修改两处参数。
- 不要同时运行 SLAM Toolbox 和导航中的 AMCL（都可能争夺 `map -> odom`）。

## 2. 放置和编译

把本压缩包 `ros2_ws/src/` 下的三个包拷到树莓派现有 `~/ros2_ws/src/`。**不要覆盖你的电机驱动、micro-ROS、`oradar_lidar` 或已保存的地图；先备份已有同名包。**

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y python3-picamera2 python3-pyzbar libzbar0 ros-jazzy-cv-bridge
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select qr_msgs qr_vision robot_nav --symlink-install
source install/setup.bash
ros2 pkg executables robot_nav
```

原工程中的 Nav2 依赖（包括 MPPI、route/docking 插件）也必须事先安装。若 `rosdep` 发现缺少相关系统依赖，先补齐再编译，不应忽略失败信息。请在**新的终端**执行 `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash`。

## 3. 先验证硬件接口，不启动车辆

```bash
ros2 topic list -t
ros2 topic info /cmd_vel -v
ros2 topic echo /scan --once --qos-reliability best_effort
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser
```

必须确认 `/scan` 的 `header.frame_id` 对应真实雷达 TF；`common.launch.py` 中的 `laser_x/y/z` 和 `camera_x/y/z` 均为原项目的占位安装参数。如果已有其他节点发布相同的静态 TF，避免重复发布。

## 4. 相机和二维码（先只识别）

```bash
ros2 launch qr_vision qr_vision.launch.py
```

如果已有别的节点发布 `/image_raw`，改用 `use_camera:=false`，避免同时争用实体相机。

```bash
ros2 topic echo /qr_result
ros2 topic pub --once /target_code std_msgs/msg/String "{data: 'A01'}"
```

将 `A01` 替换成真实标签。识别节点使用严格目标匹配：指定目标未出现在画面时，`found=false`，不会对准错误货架；不指定目标时仍选择画面中宽度最大的码。相机像素对位参数保留原 `qr_vision/config/qr.yaml`，实机必须校准。对位默认不启用，千万不要在未校准时发布 `align_enable=true`。

## 5. 建图及导航启动（实车停机状态）

底层里程计和 `/scan`、TF 正常后，建图：

```bash
ros2 launch robot_nav mapping.launch.py
```

建图和 AMCL 不可同时运行。建图完成可保存：

```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/robot_nav/maps/room
```

停止建图，随后用真实保存的绝对地图路径启动：

```bash
ros2 launch robot_nav navigation.launch.py map:=$HOME/ros2_ws/src/robot_nav/maps/room.yaml
```

**本版导航启动默认 `control_mode=stop`，不会自动放行电机速度。** 先检查 Nav2 节点 `active`、`/compute_path_to_pose`、`/navigate_to_pose` 和 `/cmd_vel_nav_safe` 的发布/订阅关系。`/cmd_vel_nav_safe` 曾在仿真中无消息输出，具体原因没有被实测排除，不能假设实车一定正常。

## 6. 默认只规划；明确允许后才可驱动

从实车 RViz 的 `map` 坐标系读取目标点，先规划：

```bash
ros2 run robot_nav nav_goal --x X --y Y --yaw 0.0 --plan-only
```

只有已确认急停、周边空旷、轮廓、控制输出类型及碰撞监测均正常，并由现场人员看护时，才**依次**：

```bash
ros2 topic pub --once /control_mode std_msgs/msg/String "{data: 'nav'}"
ros2 run robot_nav nav_goal --x X --y Y --yaw 0.0 --drive
```

`--drive` 是本版显式实车运动开关；不带该参数的 `nav_goal` 默认只规划。紧急停止模式：

```bash
ros2 topic pub --once /control_mode std_msgs/msg/String "{data: 'stop'}"
```

取消导航目标后再切换到视觉对位模式，避免多个控制源同时指挥小车。不要同时启动两个 `cmd_vel_mux`，也不要让底盘直连未经安全切换的 `/cmd_vel_nav`。

## 7. 当前配置边界

- `robot_nav/config/nav2_params.yaml` 保留实车 AMCL、MPPI 和雷达输入 `/scan`；`local_costmap.width` 和 `.height` 按你的要求设为 YAML 整数 `2`，不是浮点数 `2.0`。
- `nav_goal` 已正确区分 `ComputePathToPose.goal` 和 `NavigateToPose.pose`，并防止重复 `rclpy.shutdown()`。
- `cmd_vel_mux` 切换速度来源时会清除旧指令，导航启动默认 STOP；软件停止仍需底层驱动看门狗和硬件急停配合。
- **本文件不是仿真工程的复制品**：仿真的 `/scan_localization`、`/warehouse/control_mode`、`TwistStamped`、`use_sim_time=true` 不应直接搬入实体车。
- 实车传感器型号、ROS 2 发行版、底盘电机驱动消息类型、TF、尺寸和地图仍需在树莓派上确认。因此无法保证未经实车联调就完整自主行驶。

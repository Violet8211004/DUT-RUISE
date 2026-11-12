"""按模式选择唯一的速度来源，再发布到 /cmd_vel。"""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String


class CmdVelMux(Node):
    def __init__(self):
        super().__init__("cmd_vel_mux")
        self.declare_parameter("initial_mode", "stop")
        self.declare_parameter("timeout_sec", 0.5)
        self.mode = self.get_parameter("initial_mode").value
        self.latest = {}
        self.publisher = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(String, "control_mode", self.on_mode, 10)
        for name in ("nav", "align", "teleop"):
            self.create_subscription(
                Twist,
                f"cmd_vel_{name}" if name != "nav" else "cmd_vel_nav_safe",
                lambda msg, source=name: self.on_twist(source, msg),
                10,
            )
        self.create_timer(0.05, self.on_timer)
        self.get_logger().info(f"速度模式：{self.mode}。可选 nav、align、teleop、stop")

    def on_mode(self, msg):
        mode = msg.data.strip()
        if mode not in ("nav", "align", "teleop", "stop"):
            self.get_logger().warning(f"未知模式：{mode}")
            return
        if self.mode != mode:
            self.latest.clear()  # prevent replaying stale speed when switching sources
        self.mode = mode
        self.get_logger().info(f"切换到 {mode}")

    def on_twist(self, source, msg):
        self.latest[source] = (self.get_clock().now(), msg)

    def on_timer(self):
        out = Twist()
        if self.mode in self.latest:
            stamp, msg = self.latest[self.mode]
            age = (self.get_clock().now() - stamp).nanoseconds * 1e-9
            if age <= float(self.get_parameter("timeout_sec").value):
                out = msg
        self.publisher.publish(out)


def main():
    rclpy.init()
    node = CmdVelMux()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

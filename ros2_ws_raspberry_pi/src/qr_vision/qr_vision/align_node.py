"""根据二维码偏差发布对位速度。只在 align_enable 为真时发布。"""

from rclpy.duration import Duration
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Bool

from qr_msgs.msg import QrResult
from qr_vision.control import alignment_twist


class AlignNode(Node):
    def __init__(self):
        super().__init__("align_node")
        self.declare_parameter("dx_tol", 40)
        self.declare_parameter("target_width", 200)
        self.declare_parameter("kp_yaw", 0.003)
        self.declare_parameter("kp_lin", 0.0008)
        self.declare_parameter("max_yaw", 0.35)
        self.declare_parameter("max_lin", 0.06)
        self.declare_parameter("stale_sec", 0.4)

        self.enabled = False
        self.last = None
        self.last_stamp = None
        self.publisher = self.create_publisher(Twist, "cmd_vel_align", 10)
        self.create_subscription(Bool, "align_enable", self.on_enable, 10)
        self.create_subscription(QrResult, "qr_result", self.on_qr, 10)
        self.create_timer(0.1, self.on_timer)

    def on_enable(self, msg):
        self.enabled = bool(msg.data)
        if not self.enabled:
            self.publisher.publish(Twist())

    def on_qr(self, msg):
        self.last = msg
        self.last_stamp = self.get_clock().now()

    def on_timer(self):
        if not self.enabled:
            return

        fresh = False
        if self.last is not None and self.last_stamp is not None:
            age = self.get_clock().now() - self.last_stamp
            fresh = age < Duration(seconds=float(self.get_parameter("stale_sec").value))

        found = fresh and self.last.found
        aligned = fresh and self.last.aligned
        dx = self.last.dx if fresh else 0
        width_px = self.last.width_px if fresh else 0
        linear, angular = alignment_twist(
            found=found,
            aligned=aligned,
            dx=dx,
            width_px=width_px,
            dx_tol=int(self.get_parameter("dx_tol").value),
            target_width=int(self.get_parameter("target_width").value),
            kp_yaw=float(self.get_parameter("kp_yaw").value),
            kp_lin=float(self.get_parameter("kp_lin").value),
            max_yaw=float(self.get_parameter("max_yaw").value),
            max_lin=float(self.get_parameter("max_lin").value),
        )
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        self.publisher.publish(twist)


def main():
    rclpy.init()
    node = AlignNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

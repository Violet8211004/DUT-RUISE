"""用速度指令积分出临时里程计。

这是航迹推算，不是编码器。底盘开始发布真实 /odom 和 odom 到 base_link 的坐标变换后，必须停止本节点。
"""

import math

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class CmdVelOdom(Node):
    def __init__(self):
        super().__init__("cmdvel_odom")
        self.declare_parameter("cmd_vel_topic", "cmd_vel")
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.vx = 0.0
        self.wz = 0.0
        self.last_time = self.get_clock().now()
        self.odom_pub = self.create_publisher(Odometry, "odom", 10)
        self.tf_pub = TransformBroadcaster(self)
        topic = self.get_parameter("cmd_vel_topic").value
        self.create_subscription(Twist, topic, self.on_twist, 10)
        self.create_timer(0.05, self.on_timer)
        self.get_logger().warning("正在用速度积分代替编码器里程计，仅供建图前期使用")

    def on_twist(self, msg):
        self.vx = msg.linear.x
        self.wz = msg.angular.z

    def on_timer(self):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now
        if dt <= 0.0 or dt > 1.0:
            return

        self.yaw += self.wz * dt
        self.x += self.vx * math.cos(self.yaw) * dt
        self.y += self.vx * math.sin(self.yaw) * dt

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.yaw * 0.5)
        odom.pose.pose.orientation.w = math.cos(self.yaw * 0.5)
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.angular.z = self.wz
        self.odom_pub.publish(odom)

        transform = TransformStamped()
        transform.header.stamp = odom.header.stamp
        transform.header.frame_id = "odom"
        transform.child_frame_id = "base_link"
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.rotation = odom.pose.pose.orientation
        self.tf_pub.sendTransform(transform)


def main():
    rclpy.init()
    node = CmdVelOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

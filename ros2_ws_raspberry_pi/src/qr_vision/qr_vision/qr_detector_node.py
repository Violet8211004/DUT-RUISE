"""订阅图像，用 pyzbar 解码，并计算几何量。"""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String

from qr_vision.geometry import CodeHit, measure

try:
    from cv_bridge import CvBridge
    from pyzbar.pyzbar import decode as decode_codes
except ImportError:  # 允许在没有这些库的机器上做语法检查
    CvBridge = None
    decode_codes = None

from qr_msgs.msg import QrResult


class QrDetectorNode(Node):
    def __init__(self):
        super().__init__("qr_detector_node")
        if CvBridge is None or decode_codes is None:
            raise RuntimeError("需要安装 cv_bridge 和 pyzbar 后才能运行二维码节点")

        self.declare_parameter("target_code", "")
        self.declare_parameter("dx_tol", 40)
        self.declare_parameter("target_width", 200)
        self.declare_parameter("width_tol", 30)
        self.bridge = CvBridge()
        self.target_code = self.get_parameter("target_code").value

        self.publisher = self.create_publisher(QrResult, "qr_result", 10)
        self.create_subscription(Image, "image_raw", self.on_image, qos_profile_sensor_data)
        self.create_subscription(String, "target_code", self.on_target, 10)

    def on_target(self, msg):
        self.target_code = msg.data.strip()

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        hits = []
        for item in decode_codes(frame):
            hits.append(
                CodeHit(
                    data=item.data.decode("utf-8", errors="replace").strip(),
                    left=item.rect.left,
                    top=item.rect.top,
                    width=item.rect.width,
                    height=item.rect.height,
                )
            )
        result = measure(
            image_width=frame.shape[1],
            hits=hits,
            target_code=self.target_code,
            dx_tol=int(self.get_parameter("dx_tol").value),
            target_width=int(self.get_parameter("target_width").value),
            width_tol=int(self.get_parameter("width_tol").value),
        )
        out = QrResult()
        out.header.stamp = msg.header.stamp
        out.header.frame_id = msg.header.frame_id
        out.found = result["found"]
        out.code = result["code"]
        out.dx = result["dx"]
        out.width_px = result["width_px"]
        out.aligned = result["aligned"]
        self.publisher.publish(out)


def main():
    rclpy.init()
    node = QrDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

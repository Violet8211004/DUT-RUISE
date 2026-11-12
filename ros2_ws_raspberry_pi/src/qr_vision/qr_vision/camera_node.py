"""Camera Module 3 取图，发布到 image_raw。"""

import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class CameraNode(Node):
    def __init__(self):
        super().__init__("camera_node")
        self.declare_parameter("width", 1280)
        self.declare_parameter("height", 720)
        self.declare_parameter("fps", 10.0)
        self.declare_parameter("frame_id", "camera_link")
        self.declare_parameter("color_encoding", "rgb8")

        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, "image_raw", qos_profile_sensor_data)
        self.camera = self._open_camera()
        period = 1.0 / float(self.get_parameter("fps").value)
        self.create_timer(period, self.on_timer)

    def _open_camera(self):
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError(
                "未安装 picamera2。在树莓派上执行：sudo apt install python3-picamera2"
            ) from exc

        width = int(self.get_parameter("width").value)
        height = int(self.get_parameter("height").value)
        camera = Picamera2()
        config = camera.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"},
            buffer_count=2,
        )
        camera.configure(config)
        camera.start()
        self.get_logger().info(f"相机已打开：{width}x{height}")
        return camera

    def on_timer(self):
        frame = self.camera.capture_array()
        encoding = self.get_parameter("color_encoding").value
        if encoding == "bgr8" and frame.ndim == 3 and frame.shape[2] >= 3:
            frame = frame[:, :, ::-1]
        msg = self.bridge.cv2_to_imgmsg(frame[:, :, :3], encoding=encoding)
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.get_parameter("frame_id").value
        self.publisher.publish(msg)

    def destroy_node(self):
        camera = getattr(self, "camera", None)
        if camera is not None:
            camera.stop()
        super().destroy_node()


def main():
    rclpy.init()
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

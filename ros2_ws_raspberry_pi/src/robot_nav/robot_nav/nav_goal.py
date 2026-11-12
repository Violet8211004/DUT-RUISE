"""ROS 2 Jazzy single-goal Nav2 test client; defaults to planning only.

ComputePathToPose requires Goal.goal; NavigateToPose requires Goal.pose.
Real robot: uses wall/ROS time, NEVER sim time. --drive must be explicit.
"""
import argparse
import math
import sys

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose, NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


def pose_in_map(node, x, y, yaw):
    msg = PoseStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = "map"
    msg.pose.position.x = float(x)
    msg.pose.position.y = float(y)
    msg.pose.orientation.z = math.sin(yaw / 2.0)
    msg.pose.orientation.w = math.cos(yaw / 2.0)
    return msg


def call_action(node, x, y, yaw, drive):
    action_type = NavigateToPose if drive else ComputePathToPose
    name = "/navigate_to_pose" if drive else "/compute_path_to_pose"
    client = ActionClient(node, action_type, name)
    if not client.wait_for_server(timeout_sec=15.0):
        node.get_logger().error(f"Nav2 action not available: {name}")
        return False

    goal = action_type.Goal()
    if drive:
        goal.pose = pose_in_map(node, x, y, yaw)  # NavigateToPose uses pose
    else:
        goal.goal = pose_in_map(node, x, y, yaw)  # ComputePathToPose uses goal
        goal.use_start = False
        goal.planner_id = "GridBased"

    handle = None
    try:
        response = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, response)
        handle = response.result()
        if handle is None or not handle.accepted:
            node.get_logger().error("Goal rejected")
            return False
        node.get_logger().info("Goal accepted: " + ("DRIVE" if drive else "PLAN ONLY"))
        answer = handle.get_result_async()
        rclpy.spin_until_future_complete(node, answer)
        reply = answer.result()
        if reply is None:
            node.get_logger().error("No action result (ROS context might be stopped)")
            return False
        if reply.status != GoalStatus.STATUS_SUCCEEDED:
            code = getattr(reply.result, "error_code", None)
            message = getattr(reply.result, "error_msg", "")
            node.get_logger().error(
                f"Nav2 failed: status={reply.status}, error_code={code}, error_msg={message}"
            )
            return False
        if drive:
            node.get_logger().info("NavigateToPose reported SUCCESS; verify physical stop and pose.")
        else:
            route = reply.result.path
            node.get_logger().info(
                f"Path computed: {len(route.poses)} poses, frame={route.header.frame_id}"
            )
            return len(route.poses) >= 2
        return True
    except KeyboardInterrupt:
        node.get_logger().warning("Interrupted. Send /control_mode stop immediately.")
        if handle is not None and rclpy.ok():
            try:
                cf = handle.cancel_goal_async()
                rclpy.spin_until_future_complete(node, cf, timeout_sec=2.0)
            except Exception as exc:
                node.get_logger().error(f"Cancel could not be confirmed: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Real-robot Nav2 planning or explicit drive test")
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--y", type=float, required=True)
    parser.add_argument("--yaw", type=float, default=0.0)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan-only", action="store_true", help="only compute a path (default)")
    mode.add_argument("--drive", action="store_true", help="send REAL driving goal; enable nav mux separately")
    opts = parser.parse_args(sys.argv[1:])
    rclpy.init()
    node = Node("robot_nav_goal")
    try:
        success = call_action(node, opts.x, opts.y, opts.yaw, drive=opts.drive)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

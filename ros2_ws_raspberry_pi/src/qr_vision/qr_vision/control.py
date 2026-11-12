"""近距离对位的比例控制。

先消除左右偏差，再沿前进方向修正距离。
dx 向右为正；角速度逆时针为正，因此码在右侧时角速度为负。
像素宽度小于目标值表示还太远，线速度为正。
已经对准或丢失目标时速度为零。
"""


def _clamp(value, limit):
    return max(-limit, min(limit, value))


def alignment_twist(
    found,
    aligned,
    dx,
    width_px,
    dx_tol,
    target_width,
    kp_yaw,
    kp_lin,
    max_yaw,
    max_lin,
):
    if not found or aligned:
        return 0.0, 0.0

    yaw = _clamp(-kp_yaw * dx, max_yaw)
    if abs(dx) > dx_tol:
        return 0.0, yaw

    forward = _clamp(kp_lin * (target_width - width_px), max_lin)
    return forward, yaw

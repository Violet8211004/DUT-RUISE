"""二维码在图像中的几何量。

算法：若指定目标编号，则先严格筛选该编号；否则取像素宽度最大的码（通常是最近的）。
用码中心相对图像中心的水平偏差表示左右，用像素宽度粗略表示远近。
偏差和宽度同时落在容差内，并且内容与目标编号一致时，判定为对准。
"""


class CodeHit:
    def __init__(self, data, left, top, width, height):
        self.data = data
        self.left = left
        self.top = top
        self.width = width
        self.height = height


def measure(image_width, hits, target_code, dx_tol, target_width, width_tol):
    if not hits:
        return {
            "found": False,
            "code": "",
            "dx": 0,
            "width_px": 0,
            "aligned": False,
        }

    # When a target is specified, reject unrelated codes (even if they are larger).
    matching_hits = [hit for hit in hits if hit.data == target_code] if target_code else hits
    if not matching_hits:
        return {
            "found": False,
            "code": "",
            "dx": 0,
            "width_px": 0,
            "aligned": False,
        }

    best = max(matching_hits, key=lambda hit: hit.width)
    center_x = best.left + best.width / 2.0
    dx = int(round(center_x - image_width / 2.0))
    aligned = (
        abs(dx) <= dx_tol
        and abs(best.width - target_width) <= width_tol
    )
    return {
        "found": True,
        "code": best.data,
        "dx": dx,
        "width_px": int(best.width),
        "aligned": aligned,
    }

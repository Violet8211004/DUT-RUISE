import os
from glob import glob

from setuptools import find_packages, setup

package_name = "qr_vision"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="student",
    maintainer_email="student@local",
    description="相机取图、二维码解码和近距离对位。",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "camera_node = qr_vision.camera_node:main",
            "qr_detector_node = qr_vision.qr_detector_node:main",
            "align_node = qr_vision.align_node:main",
        ],
    },
)

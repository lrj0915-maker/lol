"""统一路径管理 — 兼容开发环境与 PyInstaller 打包环境。"""

import os
import sys


def get_app_root() -> str:
    """可写数据根目录。

    - 打包后：exe 所在目录（持久化，不会被清理）
    - 开发时：项目根目录（backend 的上级目录）
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_root() -> str:
    """只读资源根目录。

    - 打包后：sys._MEIPASS（PyInstaller 临时解压目录）
    - 开发时：项目根目录（同 get_app_root）
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

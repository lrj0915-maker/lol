"""统一日志模块 — stdout + 文件轮转"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from paths import get_app_root

_LOG_FORMAT = '[%(name)s] %(message)s'
_FILE_FORMAT = '%(asctime)s [%(name)s] %(levelname)s %(message)s'

# 日志目录：应用根/data/logs（打包后为 exe 所在目录）
_LOG_DIR = os.path.join(get_app_root(), 'data', 'logs')
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, 'app.log')

# 共享的文件 handler（所有 logger 复用同一个文件）
_file_handler = None


def _get_file_handler() -> RotatingFileHandler:
    global _file_handler
    if _file_handler is None:
        _file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        )
        _file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
        _file_handler.setLevel(logging.DEBUG)
    return _file_handler


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger，输出到 stdout + 文件"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # stdout handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(stream_handler)
        # file handler
        logger.addHandler(_get_file_handler())
        logger.setLevel(logging.DEBUG)
    return logger

"""
统一日志配置。

集中初始化根日志器，保证所有模块日志格式一致。
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """配置根日志器，输出到 stdout，统一格式。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    # 清空可能已有的 handler，避免重复输出
    root.handlers = [handler]
    root.setLevel(level)

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_dir: str = "logs", log_filename: str = "app.log"):
    """配置全局控制台与本地文件轮转日志 (单文件 10MB，保留 5 个历史文件)"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    log_filepath = os.path.join(log_dir, log_filename)

    formatter = logging.Formatter(
        "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # 文件轮转 Handler
    file_handler = RotatingFileHandler(
        filename=log_filepath,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    logging.info(f"AlphaScout 日志模块初始化完成，存储路径: {log_filepath}")
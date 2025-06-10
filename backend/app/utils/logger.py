import logging
import sys
import os
from pathlib import Path

def setup_logger():
    """设置日志记录器"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger("ai_test_generator")
    logger.setLevel(logging.INFO)
    
    # 防止重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 创建全局日志记录器
logger = setup_logger()

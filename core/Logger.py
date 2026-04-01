import logging
import os
import sys
from datetime import datetime

def setup_logger():
    """
    配置全局日志系统，支持控制台彩色输出和文件持久化
    """
    # 确定日志存放路径 (Quant/logs)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, 'logs')
    
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            # 如果无法创建logs目录（如权限问题），则回退到当前目录
            log_dir = os.path.dirname(os.path.abspath(__file__))

    # 创建命名空间唯一的logger
    logger = logging.getLogger('QuantCore')
    logger.setLevel(logging.DEBUG)

    # 如果已经有handler，不再重复添加
    if logger.handlers:
        return logger

    # 1. 控制台 Handler (输出 INFO 及以上级别)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # 2. 文件 Handler (输出 DEBUG 及以上级别)
    log_filename = f"quant_log_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    
    try:
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file at {log_filepath}: {e}")

    logger.addHandler(console_handler)
    
    return logger

# 创建全局唯一的 logger 实例
logger = setup_logger()

if __name__ == "__main__":
    logger.info("Logger test: Standard Info")
    logger.debug("Logger test: Debug Message (File Only)")
    logger.error("Logger test: Error Message")

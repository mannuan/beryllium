# -*- coding:utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler
import os
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_logger(logs_file_name="00000000", is_save_logs=False):
    """
    日志文件
    :param logs_file_name:
    :param is_save_logs:
    :return:
    """
    print("Start print log")
    if is_save_logs:
        if not os.path.exists("logs"):
            os.mkdir("logs")
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    if is_save_logs:
        handler = TimedRotatingFileHandler(filename=os.path.join("logs", "log_%s" % logs_file_name),
                                           when="h", interval=1, backupCount=7)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        logger.addHandler(handler)
        logger.addHandler(console)
    return logger


if __name__ == "__main__":
    logger = get_logger()
    logger.error("123")

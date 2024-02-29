
import logging
from datetime import datetime


class Logger():

    def __init__(self, name):
        # 创建一个logger
        self.logger = logging.getLogger(name)
        # self.logger = logging.getLogger()  # 如果不指定name,项目中创建n多个Logger对象时,调用self.debug()时,就相当于会写入n份。
        self.logger.setLevel(logging.DEBUG)

        # 创建一个handler，用于写入日志文件
        log_path = './Logs/'
        today = datetime.now().strftime('%Y%m%d')
        logfile = log_path + str(today) + '_debug.log'

        fh = logging.FileHandler(logfile, mode='a')

        # 定义handler的输出格式
        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        fh.setFormatter(formatter)

        # 将logger添加到handler里面
        self.logger.addHandler(fh)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

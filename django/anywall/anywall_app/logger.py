import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Create a rotating file handler
    log_file = f"C:\\Anywall\\logs\\Anywall_{datetime.now().strftime('%Y-%m-%d')}.log"
    handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=1)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Base logs directory
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Standard log format
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

# Default max size per log file (in bytes) and backup count (for rotation)
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

def get_server_logger():
    """Sets up and returns the main server logger."""
    logger = logging.getLogger('server')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        server_log_path = os.path.join(LOG_DIR, f"server_session_{timestamp}.log")

        file_handler = RotatingFileHandler(server_log_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def get_job_logger(job_id):
    """Sets up and returns a logger specific to a transcription job."""
    logger = logging.getLogger(f"job_{job_id}")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_log_path = os.path.join(LOG_DIR, f"transcribe_{job_id}_{timestamp}.log")

        file_handler = RotatingFileHandler(job_log_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

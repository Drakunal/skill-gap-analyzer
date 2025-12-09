import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y_%m_%d")
log_file = os.path.join(LOG_DIR, f"{today}.log")

logger = logging.getLogger("skill_gap_analyzer")
logger.setLevel(logging.INFO)

# IMPORTANT: Prevent logs from propagating to Uvicorn/FastAPI console
logger.propagate = False

# Remove any existing handlers (avoids duplicates)
if logger.hasHandlers():
    logger.handlers.clear()

# File handler only (no console handler)
file_handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

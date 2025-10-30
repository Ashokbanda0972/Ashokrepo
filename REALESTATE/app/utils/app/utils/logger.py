import logging
import os
from datetime import datetime

LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)
date = datetime.utcnow().strftime("%Y-%m-%d")
logfile = os.path.join(LOG_DIR, f"app_{date}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(logfile),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("dev_leads")

from app.utils.config_loader import CONFIG
from app.utils.logger import logger
import os

def verify():
    missing = [k for k,v in CONFIG.items() if v is None]
    if missing:
        logger.warning("Missing env vars: %s", missing)
    else:
        logger.info("All env vars present")
    # check google credentials file
    gp = CONFIG["GOOGLE_CREDENTIALS_PATH"]
    if not gp or not os.path.exists(gp):
        logger.warning("Google credentials not found at %s", gp)
    else:
        logger.info("Google credentials found")

if __name__ == "__main__":
    verify()

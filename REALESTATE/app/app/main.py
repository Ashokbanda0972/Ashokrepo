from app.dev_pipeline import run_pipeline
from app.utils.logger import logger

if __name__ == "__main__":
    logger.info("Manual start")
    run_pipeline()

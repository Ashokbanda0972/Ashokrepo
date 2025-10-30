from apscheduler.schedulers.blocking import BlockingScheduler
from app.dev_pipeline import run_pipeline
import logging
import pytz

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def start_scheduler():
    sched = BlockingScheduler(timezone=pytz.timezone("America/New_York"))
    # Daily at 2am
    sched.add_job(run_pipeline, "cron", hour=2, minute=0, id="daily_scan")
    try:
        logger.info("Scheduler starting")
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    start_scheduler()

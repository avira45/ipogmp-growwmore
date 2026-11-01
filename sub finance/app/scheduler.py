import datetime
import threading
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.scraper import fetch_live_ipo_gmp
from app.storage import save_ipos, load_ipos

logger = logging.getLogger(__name__)

# Lock to avoid concurrent scraper executions
_sync_lock = threading.Lock()
_is_syncing = False

scheduler = BackgroundScheduler(daemon=True)

def sync_daily_gmp(force: bool = False):
    """Execute the daily scrape and update storage."""
    global _is_syncing
    if not _sync_lock.acquire(blocking=False):
        logger.warning("Sync already in progress; skipping trigger.")
        return {"status": "in_progress", "message": "A sync job is already currently running."}

    _is_syncing = True
    try:
        logger.info("Starting Daily IPO GMP Sync...")
        data = fetch_live_ipo_gmp()
        if data:
            result = save_ipos(data)
            logger.info("Daily IPO GMP Sync completed successfully with %d IPOs.", len(data))
            return {
                "status": "success",
                "count": len(data),
                "last_updated": result.get("last_updated"),
                "date": result.get("date")
            }
        else:
            logger.warning("Daily scrape returned no items.")
            return {"status": "warning", "message": "Scraper did not find any IPO records. Retaining previous data."}
    except Exception as e:
        logger.error("Exception during daily sync: %s", e)
        return {"status": "error", "message": str(e)}
    finally:
        _is_syncing = False
        _sync_lock.release()

def is_sync_needed_today() -> bool:
    """Check if we already have an update for today."""
    current = load_ipos()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return current.get("date") != today_str or not current.get("ipos")

def start_scheduler(hour: int = 9, minute: int = 30):
    """
    Start the background daily scheduler.
    Default runs daily at 09:30 AM (IST/local time).
    """
    if not scheduler.running:
        # Schedule daily once per day trigger
        scheduler.add_job(
            sync_daily_gmp,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_ipo_gmp_job",
            name="Daily IPO GMP Scrape",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler started: Daily GMP sync scheduled for %02d:%02d daily.", hour, minute)

        # Check if an initial sync is needed immediately
        if is_sync_needed_today():
            logger.info("No data found for today. Triggering initial startup sync...")
            threading.Thread(target=sync_daily_gmp, daemon=True).start()

def shutdown_scheduler():
    """Cleanly shut down scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

from apscheduler.triggers.date import DateTrigger

from app.config import DELIVERY_PERIOD_EVENING, DELIVERY_PERIOD_MORNING, get_settings
from app.pipeline import run_morning_evening_job

logger = logging.getLogger(__name__)


def create_scheduler() -> BlockingScheduler:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.scheduler_timezone)

    scheduler.add_job(
        _job_wrapper,
        CronTrigger(
            hour=settings.morning_digest_hour,
            minute=settings.morning_digest_minute,
        ),
        id="morning_digest",
        kwargs={"period": DELIVERY_PERIOD_MORNING},
        replace_existing=True,
    )
    scheduler.add_job(
        _job_wrapper,
        CronTrigger(
            hour=settings.evening_digest_hour,
            minute=settings.evening_digest_minute,
        ),
        id="evening_digest",
        kwargs={"period": DELIVERY_PERIOD_EVENING},
        replace_existing=True,
    )
    if settings.run_job_on_start:
        scheduler.add_job(
            _job_wrapper,
            DateTrigger(run_date=datetime.now() + timedelta(seconds=5)),
            id="startup_digest",
            kwargs={"period": DELIVERY_PERIOD_EVENING},
            replace_existing=True,
        )
    return scheduler


def _job_wrapper(period: str) -> None:
    import asyncio

    logger.info("scheduled job start period=%s", period)
    asyncio.run(run_morning_evening_job(period))
    logger.info("scheduled job done period=%s", period)


def start_scheduler() -> None:
    scheduler = create_scheduler()
    logger.info("APScheduler started (timezone=%s)", get_settings().scheduler_timezone)
    scheduler.start()

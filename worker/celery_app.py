from celery import Celery
from backend import config

celery_app = Celery(
    "image_scraper",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
    include=["worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
)

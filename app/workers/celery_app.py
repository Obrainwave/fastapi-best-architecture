# app/workers/celery_app.py
from celery import Celery

from app.core.config import settings

celery_app = Celery("muvielive", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

celery_app.conf.update(
    task_serializer="json", result_serializer="json", accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,   # don't let one worker hoard several long transcode jobs
    task_time_limit=60 * 60,         # hard kill at 1 hour, a stuck ffmpeg process shouldn't hang a worker forever
)

celery_app.autodiscover_tasks(["app.workers"])
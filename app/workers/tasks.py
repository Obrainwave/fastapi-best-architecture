# app/workers/tasks.py
import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app
from app.db.base import SessionLocal
from app.services.video_processing_service import VideoProcessingService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def process_video(self, video_id: str):
    try:
        asyncio.run(_process(video_id))
    except Exception as exc:
        logger.exception("Video processing failed for %s", video_id)
        asyncio.run(_fail(video_id, str(exc)))
        raise self.retry(exc=exc, countdown=60)


async def _process(video_id: str) -> None:
    async with SessionLocal() as db:
        await VideoProcessingService(db).process(uuid.UUID(video_id))


async def _fail(video_id: str, reason: str) -> None:
    async with SessionLocal() as db:
        await VideoProcessingService(db).mark_failed(uuid.UUID(video_id), reason)
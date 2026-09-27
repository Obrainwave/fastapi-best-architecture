# app/workers/tasks.py
import asyncio
import logging
import os
import shutil
import tempfile
import uuid

from app.workers.celery_app import celery_app
from app.db.base import SessionLocal
from app.models.video import Video, VideoRendition, VideoStatus
from app.storage.factory import get_storage
from app.services.ffmpeg_service import probe_video, generate_encrypted_hls_rendition, generate_thumbnail, RENDITION_LADDER

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def process_video(self, video_id: str):
    try:
        asyncio.run(_process_video(video_id))
    except Exception as exc:
        logger.exception("Video processing failed for %s", video_id)
        asyncio.run(_mark_failed(video_id, str(exc)))
        raise self.retry(exc=exc, countdown=60)


async def _process_video(video_id: str) -> None:
    storage = get_storage()

    async with SessionLocal() as db:
        video = await db.get(Video, uuid.UUID(video_id))
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        work_dir = tempfile.mkdtemp(prefix=f"video_{video_id}_")
        try:
            source_path = os.path.join(work_dir, "source")
            with open(source_path, "wb") as f:
                f.write(await storage.read(video.source_storage_key))

            probe = probe_video(source_path)
            video.duration_seconds = int(probe.duration_seconds)

            encryption_key = os.urandom(16)
            video.encryption_key = encryption_key

            thumb_path = generate_thumbnail(source_path, work_dir, at_seconds=probe.duration_seconds * 0.1)
            thumb_key = f"videos/{video_id}/thumbnail.jpg"
            await storage.save_file(thumb_key, thumb_path, content_type="image/jpeg")
            video.thumbnail_storage_key = thumb_key

            renditions_to_build = [r for r in RENDITION_LADDER if r.height <= probe.height] or [RENDITION_LADDER[0]]
            variant_lines = []

            for ladder_entry in renditions_to_build:
                rendition_dir = os.path.join(work_dir, ladder_entry.label)
                os.makedirs(rendition_dir, exist_ok=True)

                result = generate_encrypted_hls_rendition(source_path, rendition_dir, ladder_entry, encryption_key)

                prefix = f"videos/{video_id}/{ladder_entry.label}/"
                for filename in os.listdir(rendition_dir):
                    await storage.save_file(prefix + filename, os.path.join(rendition_dir, filename), content_type="application/octet-stream")

                db.add(VideoRendition(
                    video_id=video.id, label=ladder_entry.label,
                    bandwidth=result.bandwidth, width=result.width, height=result.height,
                    playlist_storage_key=prefix + "playlist.m3u8", segment_prefix=prefix,
                ))
                variant_lines.append(
                    f"#EXT-X-STREAM-INF:BANDWIDTH={result.bandwidth},RESOLUTION={result.width}x{result.height}\n"
                    f"{ladder_entry.label}/playlist.m3u8\n"
                )

            master_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n" + "".join(variant_lines)
            await storage.save(f"videos/{video_id}/master.m3u8", master_playlist.encode(), content_type="application/vnd.apple.mpegurl")

            video.status = VideoStatus.READY
            await db.commit()
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)


async def _mark_failed(video_id: str, reason: str) -> None:
    async with SessionLocal() as db:
        video = await db.get(Video, uuid.UUID(video_id))
        if video:
            video.status = VideoStatus.FAILED
            video.failure_reason = reason[:1000]
            await db.commit()
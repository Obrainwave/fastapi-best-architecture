# app/services/video_processing_service.py
import os
import shutil
import tempfile
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import VideoStatus
from app.repositories.video_repository import VideoRepository
from app.services.ffmpeg_service import (
    probe_video, generate_encrypted_hls_rendition, generate_thumbnail, RENDITION_LADDER,
)
from app.storage.factory import get_storage


class VideoNotFoundError(Exception):
    pass


class VideoProcessingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VideoRepository(db)
        self.storage = get_storage()

    async def process(self, video_id: uuid.UUID) -> None:
        video = await self.repo.get_by_id(video_id)
        if video is None:
            raise VideoNotFoundError()

        work_dir = tempfile.mkdtemp(prefix=f"video_{video_id}_")
        try:
            source_path = os.path.join(work_dir, "source")
            with open(source_path, "wb") as f:
                f.write(await self.storage.read(video.source_storage_key))

            probe = probe_video(source_path)
            video.duration_seconds = int(probe.duration_seconds)

            encryption_key = os.urandom(16)
            video.encryption_key = encryption_key

            await self._build_thumbnail(video, source_path, work_dir, probe.duration_seconds)
            variant_lines = await self._build_renditions(video, source_path, work_dir, probe.height, encryption_key)

            master_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n" + "".join(variant_lines)
            await self.storage.save(
                f"videos/{video_id}/master.m3u8", master_playlist.encode(),
                content_type="application/vnd.apple.mpegurl",
            )

            video.status = VideoStatus.READY
            await self.db.commit()
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    async def mark_failed(self, video_id: uuid.UUID, reason: str) -> None:
        video = await self.repo.get_by_id(video_id)
        if video:
            video.status = VideoStatus.FAILED
            video.failure_reason = reason[:1000]
            await self.db.commit()

    async def _build_thumbnail(self, video, source_path: str, work_dir: str, duration_seconds: float) -> None:
        thumb_path = generate_thumbnail(source_path, work_dir, at_seconds=duration_seconds * 0.1)
        thumb_key = f"videos/{video.id}/thumbnail.jpg"
        await self.storage.save_file(thumb_key, thumb_path, content_type="image/jpeg")
        video.thumbnail_storage_key = thumb_key

    async def _build_renditions(self, video, source_path: str, work_dir: str, source_height: int, encryption_key: bytes) -> list[str]:
        renditions_to_build = [r for r in RENDITION_LADDER if r.height <= source_height] or [RENDITION_LADDER[0]]
        variant_lines = []

        for ladder_entry in renditions_to_build:
            rendition_dir = os.path.join(work_dir, ladder_entry.label)
            os.makedirs(rendition_dir, exist_ok=True)

            result = generate_encrypted_hls_rendition(source_path, rendition_dir, ladder_entry, encryption_key)

            prefix = f"videos/{video.id}/{ladder_entry.label}/"
            for filename in os.listdir(rendition_dir):
                await self.storage.save_file(
                    prefix + filename, os.path.join(rendition_dir, filename), content_type="application/octet-stream",
                )

            self.repo.add_rendition(
                video_id=video.id, label=ladder_entry.label,
                bandwidth=result.bandwidth, width=result.width, height=result.height,
                playlist_storage_key=prefix + "playlist.m3u8", segment_prefix=prefix,
            )
            variant_lines.append(
                f"#EXT-X-STREAM-INF:BANDWIDTH={result.bandwidth},RESOLUTION={result.width}x{result.height}\n"
                f"{ladder_entry.label}/playlist.m3u8\n"
            )

        return variant_lines
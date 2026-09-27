# app/services/streaming_service.py
import uuid

from app.core.config import settings
from app.storage.base import StorageBackend


class InvalidSegmentNameError(Exception):
    pass


class StreamingService:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def get_master_playlist(self, video_id: uuid.UUID, token: str) -> str:
        raw = (await self.storage.read(f"videos/{video_id}/master.m3u8")).decode()
        lines = []
        for line in raw.splitlines():
            if line.endswith("playlist.m3u8"):
                line = f"{line}?token={token}"
            lines.append(line)
        return "\n".join(lines)

    async def get_rendition_playlist(self, video_id: uuid.UUID, rendition_label: str, token: str) -> str:
        key = f"videos/{video_id}/{rendition_label}/playlist.m3u8"
        raw = (await self.storage.read(key)).decode()

        lines = []
        for line in raw.splitlines():
            if line.startswith("#EXT-X-KEY"):
                line = line.replace("KEY_PLACEHOLDER", f"/stream/{video_id}/key?token={token}")
            elif line.endswith(".ts"):
                segment_key = f"videos/{video_id}/{rendition_label}/{line}"
                line = (
                    self.storage.signed_url(segment_key, settings.SEGMENT_URL_TTL_SECONDS)
                    if settings.STORAGE_BACKEND == "s3"
                    else f"/stream/{video_id}/{rendition_label}/segments/{line}?token={token}"
                )
            lines.append(line)
        return "\n".join(lines)

    async def get_segment_bytes(self, video_id: uuid.UUID, rendition_label: str, filename: str) -> bytes:
        if not filename.startswith("segment_") or not filename.endswith(".ts"):
            raise InvalidSegmentNameError()
        return await self.storage.read(f"videos/{video_id}/{rendition_label}/{filename}")
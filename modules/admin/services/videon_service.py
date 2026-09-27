# app/services/video_service.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoStatus
from app.repositories.video_repository import VideoRepository
from app.storage.factory import get_storage

SUPPORTED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-matroska"}


class UnsupportedSourceFormatError(Exception):
    pass


class VideoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VideoRepository(db)
        self.storage = get_storage()

    async def create_from_upload(
        self, *, title: str, description: str | None, price: float, extension_price: float,
        rental_days: int, extension_days: int, content_type: str,
        local_source_path: str, original_filename: str,
    ) -> Video:
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise UnsupportedSourceFormatError()

        video = await self.repo.create(
            title=title, slug=self._slugify(title), description=description,
            price=price, extension_price=extension_price,
            rental_days=rental_days, extension_days=extension_days,
        )

        source_key = f"videos/{video.id}/source/{original_filename}"
        await self.storage.save_file(source_key, local_source_path, content_type=content_type)

        video.source_storage_key = source_key
        video.status = VideoStatus.PROCESSING
        return video

    @staticmethod
    def _slugify(title: str) -> str:
        return "-".join(title.lower().split()) + "-" + uuid.uuid4().hex[:6]
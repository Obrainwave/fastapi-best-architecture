# app/repositories/video_repository.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoRendition, VideoStatus


class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, video_id: uuid.UUID) -> Video | None:
        return await self.db.get(Video, video_id)

    async def create(
        self, *, title: str, slug: str, description: str | None,
        price: float, extension_price: float, rental_days: int, extension_days: int,
    ) -> Video:
        video = Video(
            title=title, slug=slug, description=description,
            price=price, extension_price=extension_price,
            rental_days=rental_days, extension_days=extension_days,
            status=VideoStatus.UPLOADING,
        )
        self.db.add(video)
        await self.db.flush()  # populates video.id before it's used to build a storage key
        return video

    def add_rendition(
        self, *, video_id: uuid.UUID, label: str, bandwidth: int,
        width: int, height: int, playlist_storage_key: str, segment_prefix: str,
    ) -> VideoRendition:
        rendition = VideoRendition(
            video_id=video_id, label=label, bandwidth=bandwidth,
            width=width, height=height,
            playlist_storage_key=playlist_storage_key, segment_prefix=segment_prefix,
        )
        self.db.add(rendition)
        return rendition
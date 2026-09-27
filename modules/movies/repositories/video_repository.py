import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video


class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, video_id: uuid.UUID) -> Video | None:
        return await self.db.get(Video, video_id)
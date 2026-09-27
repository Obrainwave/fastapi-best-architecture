# app/services/stream_authorization_service.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase import Purchase
from app.models.video import Video, VideoStatus
from app.repositories.purchase_repository import PurchaseRepository
from app.repositories.video_repository import VideoRepository
from app.services.stream_tokens import issue_stream_token, verify_stream_token


class VideoNotAvailableError(Exception):
    pass


class NoActiveRentalError(Exception):
    pass


class InvalidStreamTokenError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class StreamAuthorizationService:
    def __init__(self, db: AsyncSession):
        self.video_repo = VideoRepository(db)
        self.purchase_repo = PurchaseRepository(db)

    async def start_session(self, user_id: uuid.UUID, video_id: uuid.UUID) -> tuple[str, Purchase]:
        video = await self.video_repo.get_by_id(video_id)
        if video is None or video.status != VideoStatus.READY:
            raise VideoNotAvailableError()

        purchase = await self.purchase_repo.get_active(user_id, video_id)
        if purchase is None:
            raise NoActiveRentalError()

        return issue_stream_token(str(user_id), str(video_id)), purchase

    async def authorize(self, video_id: uuid.UUID, token: str) -> Video:
        try:
            user_id = verify_stream_token(token, str(video_id))
        except ValueError as exc:
            raise InvalidStreamTokenError(str(exc))

        video = await self.video_repo.get_by_id(video_id)
        if video is None:
            raise VideoNotAvailableError()

        # Re-checked on every single request, not just at token issuance, so a
        # refund or a lapsed rental cuts playback off mid-session, not on next login.
        if await self.purchase_repo.get_active(uuid.UUID(user_id), video_id) is None:
            raise NoActiveRentalError()

        return video
# app/services/purchase_service.py
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase import Purchase, PurchaseStatus
from app.models.video import Video
from app.repositories.purchase_repository import PurchaseRepository


class PurchaseService:
    def __init__(self, db: AsyncSession):
        self.repo = PurchaseRepository(db)

    async def get_by_id(self, purchase_id: uuid.UUID) -> Purchase | None:
        return await self.repo.get_by_id(purchase_id)

    async def get_active_purchase(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Purchase | None:
        return await self.repo.get_active(user_id, video_id)

    async def start_pending_purchase(self, user_id: uuid.UUID, video: Video) -> Purchase:
        return await self.repo.create_pending(user_id, video.id, video.price, video.currency)

    def activate(self, purchase: Purchase, video: Video, price_paid: float, currency: str) -> None:
        now = datetime.utcnow()
        purchase.status = PurchaseStatus.ACTIVE
        purchase.purchased_at = now
        purchase.expires_at = now + timedelta(days=video.rental_days)
        purchase.price_paid = price_paid
        purchase.currency = currency

    def extend(self, purchase: Purchase, video: Video) -> None:
        now = datetime.utcnow()
        base = purchase.expires_at if purchase.expires_at and purchase.expires_at > now else now
        purchase.expires_at = base + timedelta(days=video.extension_days)
        purchase.status = PurchaseStatus.ACTIVE
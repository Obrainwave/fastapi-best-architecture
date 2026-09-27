# app/repositories/purchase_repository.py
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase import Purchase, PurchaseStatus


class PurchaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, purchase_id: uuid.UUID) -> Purchase | None:
        return await self.db.get(Purchase, purchase_id)

    async def get_active(self, user_id: uuid.UUID, video_id: uuid.UUID) -> Purchase | None:
        result = await self.db.execute(
            select(Purchase).where(
                Purchase.user_id == user_id,
                Purchase.video_id == video_id,
                Purchase.status == PurchaseStatus.ACTIVE,
            )
        )
        purchase = result.scalar_one_or_none()
        return purchase if purchase and purchase.is_active(datetime.utcnow()) else None

    async def create_pending(self, user_id: uuid.UUID, video_id: uuid.UUID, price: float, currency: str) -> Purchase:
        purchase = Purchase(user_id=user_id, video_id=video_id, status=PurchaseStatus.PENDING, price_paid=price, currency=currency)
        self.db.add(purchase)
        await self.db.flush()  # populates purchase.id before it's used as a payment reference
        return purchase
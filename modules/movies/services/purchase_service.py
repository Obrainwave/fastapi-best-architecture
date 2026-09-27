# app/services/purchase_service.py
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase import Purchase, PurchaseStatus
from app.models.video import Video


async def get_active_purchase(db: AsyncSession, user_id: uuid.UUID, video_id: uuid.UUID) -> Purchase | None:
    result = await db.execute(
        select(Purchase).where(Purchase.user_id == user_id, Purchase.video_id == video_id, Purchase.status == PurchaseStatus.ACTIVE)
    )
    purchase = result.scalar_one_or_none()
    return purchase if purchase and purchase.is_active(datetime.utcnow()) else None


async def activate_purchase(db: AsyncSession, purchase: Purchase, video: Video, price_paid: float, currency: str) -> None:
    now = datetime.utcnow()
    purchase.status = PurchaseStatus.ACTIVE
    purchase.purchased_at = now
    purchase.expires_at = now + timedelta(days=video.rental_days)
    purchase.price_paid = price_paid
    purchase.currency = currency
    await db.commit()


async def extend_purchase(db: AsyncSession, purchase: Purchase, video: Video) -> None:
    now = datetime.utcnow()
    # Extend from whichever is later: a still-active rental keeps its remaining
    # time and the extension is added on top of it, a lapsed one starts fresh
    # from now rather than from a date that's already passed.
    base = purchase.expires_at if purchase.expires_at and purchase.expires_at > now else now
    purchase.expires_at = base + timedelta(days=video.extension_days)
    purchase.status = PurchaseStatus.ACTIVE
    await db.commit()
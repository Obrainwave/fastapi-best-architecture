# app/repositories/payment_repository.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentPurpose, PaymentStatus


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_provider_reference(self, provider_reference: str) -> Payment | None:
        result = await self.db.execute(select(Payment).where(Payment.provider_reference == provider_reference))
        return result.scalar_one_or_none()

    def create(
        self, *, user_id: uuid.UUID, video_id: uuid.UUID | None, purchase_id: uuid.UUID | None,
        purpose: PaymentPurpose, status: PaymentStatus, amount: float, currency: str,
        provider: str, provider_reference: str,
    ) -> Payment:
        payment = Payment(
            user_id=user_id, video_id=video_id, purchase_id=purchase_id,
            purpose=purpose, status=status, amount=amount, currency=currency,
            provider=provider, provider_reference=provider_reference,
        )
        self.db.add(payment)
        return payment
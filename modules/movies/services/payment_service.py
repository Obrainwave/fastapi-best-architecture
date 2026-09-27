import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentPurpose, PaymentStatus
from app.repositories.payment_repository import PaymentRepository


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.repo = PaymentRepository(db)

    async def find_by_reference(self, provider_reference: str) -> Payment | None:
        return await self.repo.get_by_provider_reference(provider_reference)

    def record(
        self, *, user_id: uuid.UUID, video_id: uuid.UUID | None, purchase_id: uuid.UUID | None,
        purpose: PaymentPurpose, status: PaymentStatus, amount: float, currency: str,
        provider: str, provider_reference: str,
    ) -> Payment:
        return self.repo.create(
            user_id=user_id, video_id=video_id, purchase_id=purchase_id,
            purpose=purpose, status=status, amount=amount, currency=currency,
            provider=provider, provider_reference=provider_reference,
        )
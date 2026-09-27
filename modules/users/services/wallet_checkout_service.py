# app/services/wallet_checkout_service.py
import uuid

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.payment import PaymentPurpose, PaymentStatus
from app.services.payment_service import PaymentService

stripe.api_key = settings.STRIPE_SECRET_KEY


class WalletCheckoutService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_service = PaymentService(db)

    async def initiate_topup(self, user_id: uuid.UUID, amount: float) -> str:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100), currency="usd",
            metadata={"user_id": str(user_id), "purpose": "wallet_topup"},
        )
        self.payment_service.record(
            user_id=user_id, video_id=None, purchase_id=None,
            purpose=PaymentPurpose.WALLET_TOPUP, status=PaymentStatus.CREATED,
            amount=amount, currency="USD",
            provider="stripe", provider_reference=intent.id,
        )
        await self.db.commit()
        return intent.client_secret
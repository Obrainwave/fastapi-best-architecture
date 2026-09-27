# app/services/purchase_checkout_service.py
import uuid

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.payment import PaymentPurpose, PaymentStatus
from app.repositories.video_repository import VideoRepository
from app.schemas.payment import PaymentMethod
from app.services.payment_service import PaymentService
from app.services.purchase_service import PurchaseService
from app.services.wallet_service import WalletService

stripe.api_key = settings.STRIPE_SECRET_KEY


class VideoNotFoundError(Exception):
    pass


class AlreadyOwnedError(Exception):
    pass


class PurchaseNotFoundError(Exception):
    pass


class PurchaseCheckoutService:
    """The one place that knows a purchase, a wallet debit, and a payment
    ledger entry have to land together in one transaction, or not at all."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.purchase_service = PurchaseService(db)
        self.wallet_service = WalletService(db)
        self.payment_service = PaymentService(db)

    async def purchase_video(self, user_id: uuid.UUID, video_id: uuid.UUID, payment_method: PaymentMethod) -> dict:
        video = await self.video_repo.get_by_id(video_id)
        if video is None:
            raise VideoNotFoundError()

        if await self.purchase_service.get_active_purchase(user_id, video_id):
            raise AlreadyOwnedError()

        purchase = await self.purchase_service.start_pending_purchase(user_id, video)

        if payment_method == PaymentMethod.WALLET:
            await self.wallet_service.debit(user_id, video.price, reference=f"purchase:{purchase.id}")
            self.payment_service.record(
                user_id=user_id, video_id=video_id, purchase_id=purchase.id,
                purpose=PaymentPurpose.PURCHASE, status=PaymentStatus.SUCCEEDED,
                amount=video.price, currency=video.currency,
                provider="wallet", provider_reference=f"wallet:{uuid.uuid4()}",
            )
            self.purchase_service.activate(purchase, video, video.price, video.currency)
            await self.db.commit()
            return {"purchase_id": purchase.id, "status": "active", "expires_at": purchase.expires_at, "client_secret": None}

        intent = stripe.PaymentIntent.create(
            amount=int(video.price * 100), currency=video.currency.lower(),
            metadata={"purchase_id": str(purchase.id), "purpose": "purchase"},
        )
        self.payment_service.record(
            user_id=user_id, video_id=video_id, purchase_id=purchase.id,
            purpose=PaymentPurpose.PURCHASE, status=PaymentStatus.CREATED,
            amount=video.price, currency=video.currency,
            provider="stripe", provider_reference=intent.id,
        )
        await self.db.commit()
        return {"purchase_id": purchase.id, "status": "pending", "expires_at": None, "client_secret": intent.client_secret}

    async def extend_purchase(self, user_id: uuid.UUID, purchase_id: uuid.UUID, payment_method: PaymentMethod) -> dict:
        purchase = await self.purchase_service.get_by_id(purchase_id)
        if purchase is None or purchase.user_id != user_id:
            raise PurchaseNotFoundError()

        video = await self.video_repo.get_by_id(purchase.video_id)

        if payment_method == PaymentMethod.WALLET:
            await self.wallet_service.debit(user_id, video.extension_price, reference=f"extension:{purchase.id}")
            self.payment_service.record(
                user_id=user_id, video_id=video.id, purchase_id=purchase.id,
                purpose=PaymentPurpose.EXTENSION, status=PaymentStatus.SUCCEEDED,
                amount=video.extension_price, currency=video.currency,
                provider="wallet", provider_reference=f"wallet:{uuid.uuid4()}",
            )
            self.purchase_service.extend(purchase, video)
            await self.db.commit()
            return {"purchase_id": purchase.id, "expires_at": purchase.expires_at, "client_secret": None}

        intent = stripe.PaymentIntent.create(
            amount=int(video.extension_price * 100), currency=video.currency.lower(),
            metadata={"purchase_id": str(purchase.id), "purpose": "extension"},
        )
        self.payment_service.record(
            user_id=user_id, video_id=video.id, purchase_id=purchase.id,
            purpose=PaymentPurpose.EXTENSION, status=PaymentStatus.CREATED,
            amount=video.extension_price, currency=video.currency,
            provider="stripe", provider_reference=intent.id,
        )
        await self.db.commit()
        return {"purchase_id": purchase.id, "expires_at": None, "client_secret": intent.client_secret}

    async def handle_stripe_webhook(self, event: dict) -> None:
        if event["type"] != "payment_intent.succeeded":
            return

        intent = event["data"]["object"]
        payment = await self.payment_service.find_by_reference(intent["id"])
        if payment is None or payment.status == PaymentStatus.SUCCEEDED:
            return

        payment.status = PaymentStatus.SUCCEEDED

        if payment.purpose == PaymentPurpose.WALLET_TOPUP:
            await self.wallet_service.credit(payment.user_id, payment.amount, reference=f"topup:{payment.id}")
        else:
            purchase = await self.purchase_service.get_by_id(payment.purchase_id)
            video = await self.video_repo.get_by_id(payment.video_id)
            if payment.purpose == PaymentPurpose.PURCHASE:
                self.purchase_service.activate(purchase, video, payment.amount, payment.currency)
            else:
                self.purchase_service.extend(purchase, video)

        await self.db.commit()
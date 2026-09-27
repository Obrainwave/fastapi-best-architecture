# app/api/purchases.py
import uuid

import stripe
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.base import get_db
from app.models.video import Video
from app.models.purchase import Purchase, PurchaseStatus
from app.models.payment import Payment, PaymentPurpose, PaymentStatus
from app.schemas.payment import PaymentMethod
from app.services import purchase_service, wallet_service

stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/videos/{video_id}/purchase")
async def initiate_purchase(
    video_id: uuid.UUID,
    payment_method: PaymentMethod = Body(embed=True),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(404, "Video not found")

    if await purchase_service.get_active_purchase(db, user.id, video_id):
        raise HTTPException(409, "You already own this video")

    purchase = Purchase(user_id=user.id, video_id=video_id, status=PurchaseStatus.PENDING, price_paid=video.price, currency=video.currency)
    db.add(purchase)
    await db.flush()

    if payment_method == PaymentMethod.WALLET:
        try:
            await wallet_service.debit(db, user.id, video.price, reference=f"purchase:{purchase.id}")
        except wallet_service.InsufficientFundsError:
            raise HTTPException(402, "Insufficient wallet balance")

        db.add(Payment(
            user_id=user.id, video_id=video_id, purchase_id=purchase.id,
            purpose=PaymentPurpose.PURCHASE, status=PaymentStatus.SUCCEEDED,
            amount=video.price, currency=video.currency,
            provider="wallet", provider_reference=f"wallet:{uuid.uuid4()}",
        ))

        # No webhook round trip, the money already moved, so activation
        # happens immediately in the same transaction as the debit.
        await purchase_service.activate_purchase(db, purchase, video, video.price, video.currency)
        return {"purchase_id": str(purchase.id), "status": "active", "expires_at": purchase.expires_at.isoformat()}

    intent = stripe.PaymentIntent.create(
        amount=int(video.price * 100), currency=video.currency.lower(),
        metadata={"purchase_id": str(purchase.id), "purpose": "purchase"},
    )
    db.add(Payment(
        user_id=user.id, video_id=video_id, purchase_id=purchase.id,
        purpose=PaymentPurpose.PURCHASE, status=PaymentStatus.CREATED,
        amount=video.price, currency=video.currency,
        provider="stripe", provider_reference=intent.id,
    ))
    await db.commit()
    return {"purchase_id": str(purchase.id), "client_secret": intent.client_secret}


@router.post("/{purchase_id}/extend")
async def initiate_extension(
    purchase_id: uuid.UUID,
    payment_method: PaymentMethod = Body(embed=True),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    purchase = await db.get(Purchase, purchase_id)
    if purchase is None or purchase.user_id != user.id:
        raise HTTPException(404, "Purchase not found")

    video = await db.get(Video, purchase.video_id)

    if payment_method == PaymentMethod.WALLET:
        try:
            await wallet_service.debit(db, user.id, video.extension_price, reference=f"extension:{purchase.id}")
        except wallet_service.InsufficientFundsError:
            raise HTTPException(402, "Insufficient wallet balance")

        db.add(Payment(
            user_id=user.id, video_id=video.id, purchase_id=purchase.id,
            purpose=PaymentPurpose.EXTENSION, status=PaymentStatus.SUCCEEDED,
            amount=video.extension_price, currency=video.currency,
            provider="wallet", provider_reference=f"wallet:{uuid.uuid4()}",
        ))

        await purchase_service.extend_purchase(db, purchase, video)
        return {"purchase_id": str(purchase.id), "expires_at": purchase.expires_at.isoformat()}

    intent = stripe.PaymentIntent.create(
        amount=int(video.extension_price * 100), currency=video.currency.lower(),
        metadata={"purchase_id": str(purchase.id), "purpose": "extension"},
    )
    db.add(Payment(
        user_id=user.id, video_id=video.id, purchase_id=purchase.id,
        purpose=PaymentPurpose.EXTENSION, status=PaymentStatus.CREATED,
        amount=video.extension_price, currency=video.currency,
        provider="stripe", provider_reference=intent.id,
    ))
    await db.commit()
    return {"client_secret": intent.client_secret}


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook signature")

    if event["type"] != "payment_intent.succeeded":
        return {"received": True}

    intent = event["data"]["object"]
    result = await db.execute(select(Payment).where(Payment.provider_reference == intent["id"]))
    payment = result.scalar_one_or_none()

    if payment is None or payment.status == PaymentStatus.SUCCEEDED:
        return {"received": True}

    payment.status = PaymentStatus.SUCCEEDED

    if payment.purpose == PaymentPurpose.WALLET_TOPUP:
        await wallet_service.credit(db, payment.user_id, payment.amount, reference=f"topup:{payment.id}")
    else:
        purchase = await db.get(Purchase, payment.purchase_id)
        video = await db.get(Video, payment.video_id)

        if payment.purpose == PaymentPurpose.PURCHASE:
            await purchase_service.activate_purchase(db, purchase, video, payment.amount, payment.currency)
        else:
            await purchase_service.extend_purchase(db, purchase, video)

    await db.commit()
    return {"received": True}
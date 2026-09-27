# app/api/purchases.py
import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.base import get_db
from app.schemas.purchase import ExtensionInitiatedResponse, ExtensionRequest, PurchaseInitiatedResponse, PurchaseRequest
from app.services.purchase_checkout_service import (
    AlreadyOwnedError, PurchaseCheckoutService, PurchaseNotFoundError, VideoNotFoundError,
)
from app.services.wallet_service import InsufficientFundsError

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/videos/{video_id}/purchase", response_model=PurchaseInitiatedResponse)
async def purchase_video(video_id: uuid.UUID, body: PurchaseRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    checkout = PurchaseCheckoutService(db)
    try:
        return await checkout.purchase_video(user.id, video_id, body.payment_method)
    except VideoNotFoundError:
        raise HTTPException(404, "Video not found")
    except AlreadyOwnedError:
        raise HTTPException(409, "You already own this video")
    except InsufficientFundsError:
        raise HTTPException(402, "Insufficient wallet balance")


@router.post("/{purchase_id}/extend", response_model=ExtensionInitiatedResponse)
async def extend_purchase(purchase_id: uuid.UUID, body: ExtensionRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    checkout = PurchaseCheckoutService(db)
    try:
        return await checkout.extend_purchase(user.id, purchase_id, body.payment_method)
    except PurchaseNotFoundError:
        raise HTTPException(404, "Purchase not found")
    except InsufficientFundsError:
        raise HTTPException(402, "Insufficient wallet balance")


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook signature")

    await PurchaseCheckoutService(db).handle_stripe_webhook(event)
    return {"received": True}
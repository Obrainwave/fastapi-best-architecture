# app/api/purchases.py
import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.base import get_db
from app.models.video import Video
from app.models.purchase import Purchase, PurchaseStatus
from app.models.payment import Payment, PaymentPurpose, PaymentStatus
from app.services import purchase_service

stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/videos/{video_id}/purchase")
async def initiate_purchase(video_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(404, "Video not found")

    if await purchase_service.get_active_purchase(db, user.id, video_id):
        raise HTTPException(409, "You already own this video")

    purchase = Purchase(user_id=user.id, video_id=video_id, status=PurchaseStatus.PENDING, price_paid=video.price, currency=video.currency)
    db.add(purchase)
    await db.flush()

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
async def initiate_extension(purchase_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    purchase = await db.get(Purchase, purchase_id)
    if purchase is None or purchase.user_id != user.id:
        raise HTTPException(404, "Purchase not found")

    video = await db.get(Video, purchase.video_id)

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
        # Unknown reference or an already-processed retry, either way this
        # makes the handler safe to call more than once for the same event.
        return {"received": True}

    payment.status = PaymentStatus.SUCCEEDED
    purchase = await db.get(Purchase, payment.purchase_id)
    video = await db.get(Video, payment.video_id)

    if payment.purpose == PaymentPurpose.PURCHASE:
        await purchase_service.activate_purchase(db, purchase, video, payment.amount, payment.currency)
    else:
        await purchase_service.extend_purchase(db, purchase, video)

    await db.commit()
    return {"received": True}


@router.post("/{video_id}/start")
async def start_stream(video_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    video = await db.get(Video, video_id)
    if video is None or video.status != VideoStatus.READY:
        raise HTTPException(404, "Video not available")

    purchase = await purchase_service.get_active_purchase(db, user.id, video_id)
    if purchase is None:
        raise HTTPException(403, "You don't have an active rental for this video")

    token = issue_stream_token(str(user.id), str(video_id))
    return {"playlist_url": f"/stream/{video_id}/master.m3u8?token={token}", "expires_at": purchase.expires_at.isoformat()}


async def _authorize(video_id: uuid.UUID, token: str, db: AsyncSession) -> Video:
    try:
        user_id = verify_stream_token(token, str(video_id))
    except ValueError as exc:
        raise HTTPException(403, str(exc))

    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(404, "Video not found")

    # Re-checked on every single request, not just when the token was issued,
    # so a refund or a lapsed rental cuts playback off mid-session, not on next login.
    if await purchase_service.get_active_purchase(db, uuid.UUID(user_id), video_id) is None:
        raise HTTPException(403, "Your rental for this video has ended")

    return video


@router.get("/{video_id}/master.m3u8")
async def get_master_playlist(video_id: uuid.UUID, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    await _authorize(video_id, token, db)
    raw = (await get_storage().read(f"videos/{video_id}/master.m3u8")).decode()

    lines = []
    for line in raw.splitlines():
        if line.endswith("playlist.m3u8"):
            line = f"{line}?token={token}"
        lines.append(line)

    return Response("\n".join(lines), media_type="application/vnd.apple.mpegurl")


@router.get("/{video_id}/{rendition_label}/playlist.m3u8")
async def get_rendition_playlist(video_id: uuid.UUID, rendition_label: str, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    await _authorize(video_id, token, db)
    storage = get_storage()
    raw = (await storage.read(f"videos/{video_id}/{rendition_label}/playlist.m3u8")).decode()

    lines = []
    for line in raw.splitlines():
        if line.startswith("#EXT-X-KEY"):
            line = line.replace("KEY_PLACEHOLDER", f"/stream/{video_id}/key?token={token}")
        elif line.endswith(".ts"):
            segment_key = f"videos/{video_id}/{rendition_label}/{line}"
            line = (
                storage.signed_url(segment_key, settings.SEGMENT_URL_TTL_SECONDS)
                if settings.STORAGE_BACKEND == "s3"
                else f"/stream/{video_id}/{rendition_label}/segments/{line}?token={token}"
            )
        lines.append(line)

    return Response("\n".join(lines), media_type="application/vnd.apple.mpegurl")


@router.get("/{video_id}/key")
async def get_encryption_key(video_id: uuid.UUID, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    video = await _authorize(video_id, token, db)
    return Response(video.encryption_key, media_type="application/octet-stream")


@router.get("/{video_id}/{rendition_label}/segments/{filename}")
async def get_segment(video_id: uuid.UUID, rendition_label: str, filename: str, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Only reached on the local storage backend, S3 segments are served straight
    from the presigned URLs generated in get_rendition_playlist above."""
    if not filename.startswith("segment_") or not filename.endswith(".ts"):
        raise HTTPException(400, "Invalid segment name")

    await _authorize(video_id, token, db)
    data = await get_storage().read(f"videos/{video_id}/{rendition_label}/{filename}")
    return Response(data, media_type="video/mp2t")
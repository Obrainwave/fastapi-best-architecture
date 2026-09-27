# app/api/streaming.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.base import get_db
from app.schemas.video import StreamStartResponse
from app.services.stream_authorization_service import (
    InvalidStreamTokenError, NoActiveRentalError, StreamAuthorizationService, VideoNotAvailableError,
)
from app.services.streaming_service import InvalidSegmentNameError, StreamingService
from app.storage.factory import get_storage

router = APIRouter(prefix="/stream", tags=["streaming"])


def _auth_error(exc: Exception) -> HTTPException:
    if isinstance(exc, InvalidStreamTokenError):
        return HTTPException(403, exc.message)
    if isinstance(exc, NoActiveRentalError):
        return HTTPException(403, "Your rental for this video has ended")
    return HTTPException(404, "Video not available")


@router.post("/{video_id}/start", response_model=StreamStartResponse)
async def start_stream(video_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        token, purchase = await StreamAuthorizationService(db).start_session(user.id, video_id)
    except (VideoNotAvailableError, NoActiveRentalError) as exc:
        raise _auth_error(exc)

    return StreamStartResponse(playlist_url=f"/stream/{video_id}/master.m3u8?token={token}", expires_at=purchase.expires_at)


@router.get("/{video_id}/master.m3u8")
async def get_master_playlist(video_id: uuid.UUID, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        await StreamAuthorizationService(db).authorize(video_id, token)
    except (VideoNotAvailableError, NoActiveRentalError, InvalidStreamTokenError) as exc:
        raise _auth_error(exc)

    body = await StreamingService(get_storage()).get_master_playlist(video_id, token)
    return Response(body, media_type="application/vnd.apple.mpegurl")


@router.get("/{video_id}/{rendition_label}/playlist.m3u8")
async def get_rendition_playlist(video_id: uuid.UUID, rendition_label: str, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        await StreamAuthorizationService(db).authorize(video_id, token)
    except (VideoNotAvailableError, NoActiveRentalError, InvalidStreamTokenError) as exc:
        raise _auth_error(exc)

    body = await StreamingService(get_storage()).get_rendition_playlist(video_id, rendition_label, token)
    return Response(body, media_type="application/vnd.apple.mpegurl")


@router.get("/{video_id}/key")
async def get_encryption_key(video_id: uuid.UUID, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        video = await StreamAuthorizationService(db).authorize(video_id, token)
    except (VideoNotAvailableError, NoActiveRentalError, InvalidStreamTokenError) as exc:
        raise _auth_error(exc)

    return Response(video.encryption_key, media_type="application/octet-stream")


@router.get("/{video_id}/{rendition_label}/segments/{filename}")
async def get_segment(video_id: uuid.UUID, rendition_label: str, filename: str, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        await StreamAuthorizationService(db).authorize(video_id, token)
    except (VideoNotAvailableError, NoActiveRentalError, InvalidStreamTokenError) as exc:
        raise _auth_error(exc)

    try:
        data = await StreamingService(get_storage()).get_segment_bytes(video_id, rendition_label, filename)
    except InvalidSegmentNameError:
        raise HTTPException(400, "Invalid segment name")

    return Response(data, media_type="video/mp2t")
# app/schemas/video.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class VideoUploadResponse(BaseModel):
    id: uuid.UUID
    status: str


class StreamStartResponse(BaseModel):
    playlist_url: str
    expires_at: datetime
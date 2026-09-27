import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Numeric, Enum, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from .video import Video


class VideoRendition(Base):
    __tablename__ = "video_renditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))

    label: Mapped[str] = mapped_column(String(20))       # "240p", "480p", "720p", "1080p"
    bandwidth: Mapped[int] = mapped_column(Integer)        # bits per second, for the master playlist
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)

    playlist_storage_key: Mapped[str] = mapped_column(String(500))  # videos/{id}/720p/playlist.m3u8
    segment_prefix: Mapped[str] = mapped_column(String(500))         # videos/{id}/720p/

    video: Mapped["Video"] = relationship(back_populates="renditions")
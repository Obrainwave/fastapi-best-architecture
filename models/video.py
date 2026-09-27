import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Numeric, Enum, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.core.enums import VideoStatus
from .video_rendition import VideoRendition


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))

    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    extension_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    rental_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    extension_days: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    status: Mapped[VideoStatus] = mapped_column(Enum(VideoStatus), default=VideoStatus.UPLOADING)

    source_storage_key: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    thumbnail_storage_key: Mapped[str | None] = mapped_column(String(500))

    # Raw AES-128 key used to encrypt every rendition's segments for this video.
    # In production wrap this with a KMS envelope key rather than storing it raw,
    # a DB dump should not be enough on its own to decrypt every title on the platform.
    encryption_key: Mapped[bytes | None] = mapped_column(LargeBinary)

    failure_reason: Mapped[str | None] = mapped_column(String(1000))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    renditions: Mapped[list["VideoRendition"]] = relationship(back_populates="video", cascade="all, delete-orphan")


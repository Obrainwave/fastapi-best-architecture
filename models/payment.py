# app/models/payment.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.core.enums import PaymentPurpose, PaymentStatus


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    video_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # null for wallet top-ups
    purchase_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("purchases.id"))

    purpose: Mapped[PaymentPurpose] = mapped_column(Enum(PaymentPurpose))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.CREATED)

    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))

    provider: Mapped[str] = mapped_column(String(20))  # "stripe" or "wallet"
    provider_reference: Mapped[str] = mapped_column(String(255), unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
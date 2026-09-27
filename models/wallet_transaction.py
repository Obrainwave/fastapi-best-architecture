import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.core.enums import WalletTransactionType
from .wallet import Wallet


class WalletTransaction(Base):
    """Append only, balance_after is a point in time snapshot, never recalculated after the fact."""

    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallets.id", ondelete="CASCADE"), index=True)

    type: Mapped[WalletTransactionType] = mapped_column(Enum(WalletTransactionType))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    balance_after: Mapped[float] = mapped_column(Numeric(10, 2))
    reference: Mapped[str] = mapped_column(String(255))  # "topup:<payment_id>", "purchase:<purchase_id>", etc

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")
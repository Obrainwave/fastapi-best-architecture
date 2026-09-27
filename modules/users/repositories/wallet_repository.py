import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, WalletTransaction, WalletTransactionType


class WalletRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_locked(self, user_id: uuid.UUID) -> Wallet | None:
        """SELECT ... FOR UPDATE, holds the row lock for the rest of this transaction."""
        result = await self.db.execute(select(Wallet).where(Wallet.user_id == user_id).with_for_update())
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID) -> Wallet:
        wallet = Wallet(user_id=user_id, balance=0, currency="USD")
        self.db.add(wallet)
        await self.db.flush()
        return wallet

    def record_transaction(self, wallet: Wallet, type_: WalletTransactionType, amount: float, reference: str) -> None:
        self.db.add(WalletTransaction(wallet_id=wallet.id, type=type_, amount=amount, balance_after=wallet.balance, reference=reference))
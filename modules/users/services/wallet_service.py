# app/services/wallet_service.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, WalletTransactionType
from app.repositories.wallet_repository import WalletRepository


class InsufficientFundsError(Exception):
    pass


class WalletService:
    def __init__(self, db: AsyncSession):
        self.repo = WalletRepository(db)

    async def get_or_create(self, user_id: uuid.UUID) -> Wallet:
        wallet = await self.repo.get_locked(user_id)
        return wallet or await self.repo.create(user_id)

    async def credit(self, user_id: uuid.UUID, amount: float, reference: str) -> Wallet:
        wallet = await self.get_or_create(user_id)
        wallet.balance = wallet.balance + amount
        self.repo.record_transaction(wallet, WalletTransactionType.CREDIT, amount, reference)
        return wallet

    async def debit(self, user_id: uuid.UUID, amount: float, reference: str) -> Wallet:
        wallet = await self.get_or_create(user_id)  # row locked for the rest of this transaction
        if wallet.balance < amount:
            raise InsufficientFundsError()
        wallet.balance = wallet.balance - amount
        self.repo.record_transaction(wallet, WalletTransactionType.DEBIT, amount, reference)
        return wallet
# app/services/wallet_service.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, WalletTransaction, WalletTransactionType
from app.core.exceptions import InsufficientFundsError


async def get_or_create_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id).with_for_update())
    wallet = result.scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=0, currency="USD")
        db.add(wallet)
        await db.flush()
    return wallet


async def credit(db: AsyncSession, user_id: uuid.UUID, amount: float, reference: str) -> Wallet:
    wallet = await get_or_create_wallet(db, user_id)
    wallet.balance = wallet.balance + amount
    db.add(WalletTransaction(
        wallet_id=wallet.id, type=WalletTransactionType.CREDIT,
        amount=amount, balance_after=wallet.balance, reference=reference,
    ))
    return wallet


async def debit(db: AsyncSession, user_id: uuid.UUID, amount: float, reference: str) -> Wallet:
    wallet = await get_or_create_wallet(db, user_id)  # row stays locked until this transaction commits
    if wallet.balance < amount:
        raise InsufficientFundsError()

    wallet.balance = wallet.balance - amount
    db.add(WalletTransaction(
        wallet_id=wallet.id, type=WalletTransactionType.DEBIT,
        amount=amount, balance_after=wallet.balance, reference=reference,
    ))
    return wallet
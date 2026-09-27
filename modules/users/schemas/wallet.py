# app/schemas/wallet.py
from pydantic import BaseModel


class WalletBalanceResponse(BaseModel):
    balance: float
    currency: str


class WalletTopupRequest(BaseModel):
    amount: float


class WalletTopupResponse(BaseModel):
    client_secret: str
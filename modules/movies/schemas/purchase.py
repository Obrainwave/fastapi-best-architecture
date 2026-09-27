# app/schemas/purchase.py
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.payment import PaymentMethod


class PurchaseRequest(BaseModel):
    payment_method: PaymentMethod


class PurchaseInitiatedResponse(BaseModel):
    purchase_id: uuid.UUID
    status: str
    expires_at: datetime | None = None
    client_secret: str | None = None


class ExtensionRequest(BaseModel):
    payment_method: PaymentMethod


class ExtensionInitiatedResponse(BaseModel):
    purchase_id: uuid.UUID
    expires_at: datetime | None = None
    client_secret: str | None = None
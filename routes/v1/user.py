from app.core.session import get_db
from app.schemas.base_schema import APIResponse
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.helpers import success
from modules.users.repositories.user_repository import UserRepository
from modules.users.schemas.user import (
    ChangePasswordRequest,
    ProfileResponse,
    UpdateProfileRequest,
)
from modules.users.services import wallet_service
from modules.users.services.user_service import UserService
from app.core.enums import PaymentPurpose, PaymentStatus

router = APIRouter(prefix="/account", tags=["Account Endpoints"])

@router.get("/profile", response_model=APIResponse[ProfileResponse])
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = UserRepository(db)
    service = UserService(repo)
    user = await service.get_profile(str(current_user.id))
    return success(True, "Profile fetched successfully", user)

@router.put("/profile", response_model=APIResponse[ProfileResponse])
async def update_profile(
    payload: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = UserRepository(db)
    service = UserService(repo)
    user = await service.update_profile(str(current_user.id), name=payload.name, phone=payload.phone)
    return success(True, "Profile updated successfully", user)

@router.put("/change-password", response_model=APIResponse[None])
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = UserRepository(db)
    service = UserService(repo)
    await service.change_password(str(current_user.id), payload.old_password, payload.new_password)
    return success(True, "Password changed successfully", None)

@router.get("/wallet", response_model=APIResponse[dict])
async def get_wallet(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    wallet = await wallet_service.get_or_create_wallet(db, user.id)
    await db.commit()
    return {"balance": float(wallet.balance), "currency": wallet.currency}


@router.post("/topup-wallet", response_model=APIResponse[dict])
async def initiate_topup(
    amount: float = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100), currency="usd",
        metadata={"user_id": str(user.id), "purpose": "wallet_topup"},
    )

    db.add(Payment(
        user_id=user.id, video_id=None, purchase_id=None,
        purpose=PaymentPurpose.WALLET_TOPUP, status=PaymentStatus.CREATED,
        amount=amount, currency="USD",
        provider="stripe", provider_reference=intent.id,
    ))
    await db.commit()

    return {"client_secret": intent.client_secret}
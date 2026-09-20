from app.core.session import get_db
from app.schemas.base_schema import APIResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.helpers import success
from modules.users.repositories.user_repository import UserRepository
from modules.users.schemas.user import (
    ChangePasswordRequest,
    ProfileResponse,
    UpdateProfileRequest,
)
from modules.users.services.user_service import UserService

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

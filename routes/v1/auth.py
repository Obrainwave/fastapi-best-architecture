from app.core.session import get_db
from app.schemas.base_schema import APIResponse
from fastapi import APIRouter, Depends, HTTPException
from modules.auth.repositories.user_repository import AuthRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.helpers import success
from modules.auth.repositories.refresh_token_repository import RefreshTokenRepository
from modules.auth.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResendCodeRequest,
    TokenResponse,
    Verify2FARequest,
    VerifyEmailRequest,
)
from modules.auth.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication Endpoints"],
)


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = AuthRepository(db)
    ref_repo = RefreshTokenRepository(db)
    service = AuthService(session=db, user_repo=repo, refresh_repo=ref_repo)
    tokens = await service.login(
        payload.username,
        payload.password,
    )

    resp = TokenResponse(**tokens)

    return success(True, "Login successful", resp)

@router.post(
    "/verify-2fa",
    response_model=APIResponse[TokenResponse],
)
async def verify_2fa(
    payload: Verify2FARequest,
    db: AsyncSession = Depends(get_db),
):
    repo = AuthRepository(db)
    ref_repo = RefreshTokenRepository(db)
    service = AuthService(session=db, user_repo=repo, refresh_repo=ref_repo)
    
    tokens = await service.verify_2fa(
        payload.temp_token,
        payload.code,
    )

    resp = TokenResponse(**tokens)

    return success(True, "2FA verified successfully", resp)

@router.post(
    "/register",
    response_model=APIResponse[RegisterResponse],
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        repo = AuthRepository(db)
        service = AuthService(session=db, user_repo=repo)
        user= await service.register(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            phone=payload.phone,
        )

        resp = RegisterResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            username=user.username,
            phone=user.phone,
        )

        return success(True, "Registration successful. Please check your email for the verification code.", resp)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = AuthRepository(db)
    ref_repo = RefreshTokenRepository(db)
    service = AuthService(session=db, user_repo=repo, refresh_repo=ref_repo)
    tokens = await service.refresh_tokens(payload.refresh_token)

    resp = TokenResponse(**tokens)

    return success(True, "Refresh token successful", resp)

@router.post(
    "/verify-email",
    response_model=APIResponse[MessageResponse],
)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = AuthRepository(db)
    service = AuthService(session=db, user_repo=repo)
    await service.verify_email(payload.email, payload.code)

    resp = MessageResponse()

    return success(True, "Email verified successfully. You can now log in.", resp)

@router.post(
    "/resend-code",
    response_model=APIResponse[MessageResponse],
)
async def resend_code(
    payload: ResendCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = AuthRepository(db)
    service = AuthService(session=db, user_repo=repo)
    await service.resend_verification_code(payload.email)

    resp = MessageResponse()

    return success(True, "Verification code resent successfully.", resp)


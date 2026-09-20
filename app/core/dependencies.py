from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from app.core.permissions import RBACService
from app.core.session import get_db
from fastapi import Depends
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

security = HTTPBearer()

from app.auth.repositories.user_repository import UserRepository

async def get_current_user(
    token=Depends(security),
    db: AsyncSession = Depends(get_db)
):

    try:

        payload = jwt.decode(
            token.credentials,
            settings.JWT_SECRET,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
            
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
            
        return user

    except JWTError:

        raise AuthenticationError(
            "Invalid token",
        )

def require_permission(permission: str):

    async def checker(
        user=Depends(get_current_user)
    ):

        if user.account == "super_admin":
            return user

        if not RBACService.has_permission(
            user,
            permission,
        ):
            raise AuthorizationError(
                "Permission denied"
            )

        return user

    return checker

def require_account(
    *allowed_accounts, 
    permission: str | None = None,
):
    async def dependency(
        user = Depends(get_current_user)
    ):
        if user.account == "super_admin":
            return user
        
        if user.account not in allowed_accounts:
            raise AuthorizationError(
                "Access forbidden"
            )
            
        if user.account == "organization" and user.is_owner:
            return user
            
        if permission:
            require_permission(permission)

        return user

    return dependency
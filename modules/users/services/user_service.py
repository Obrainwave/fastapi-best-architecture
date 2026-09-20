import uuid

from app.auth.repositories.user_repository import UserRepository

from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password


class AccountService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_profile(self, user_id: str):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def update_profile(self, user_id: str, name: str | None = None, phone: str | None = None):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        if name is not None:
            user.name = name
        if phone is not None:
            user.phone = phone
            
        return await self.user_repo.update(user)

    async def change_password(self, user_id: str, old_password: str, new_password: str):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
            
        if not verify_password(old_password, user.password_hash):
            raise ValidationError("Incorrect old password")
            
        user.password_hash = hash_password(new_password)
        return await self.user_repo.update(user)

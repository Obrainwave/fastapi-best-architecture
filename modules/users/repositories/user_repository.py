from app.auth.models.user import User
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def get_by_id(
        self,
        id: str,
    ):

        stmt = (
            select(User)
            .where(User.id == id)
        )

        result = await self.db.execute(
            stmt
        )

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ):

        stmt = select(User).where(
            User.email == email
        )

        result = await self.db.execute(
            stmt
        )

        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
    ):

        stmt = select(User).where(
            User.username == username
        )

        result = await self.db.execute(
            stmt
        )

        return result.scalar_one_or_none()

    async def get_by_login(
        self,
        login: str,
    ):

        stmt = select(User).where(
            or_(
                User.email == login,
                User.username == login,
            )
        )
        
        result = await self.db.execute(
            stmt
        )

        return result.scalar_one_or_none()
    
    async def create(self, user: User):
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User):
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def username_exists(
        self,
        username: str,
    ) -> bool:

        result = await self.db.execute(
            select(User.id).where(
                User.username == username
            )
        )

        return result.scalar_one_or_none() is not None
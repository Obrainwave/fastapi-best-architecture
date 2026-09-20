import uuid

from sqlalchemy import delete, select

from models.refresh_token import (
    RefreshToken,
)


class RefreshTokenRepository:

    def __init__(self, session):
        self.session = session

    async def create(
        self,
        token: RefreshToken,
    ):
        self.session.add(token)
        await self.session.flush()

    async def revoke(
        self,
        token_id: str | uuid.UUID,
    ):
        tid = uuid.UUID(str(token_id)) if not isinstance(token_id, uuid.UUID) else token_id
        stmt = select(
            RefreshToken
        ).where(
            RefreshToken.id == tid
        )

        result = await self.session.execute(
            stmt
        )

        token = result.scalar_one()

        token.is_revoked = True

        await self.session.commit()

    async def remove(
        self,
        user_id: str | uuid.UUID,
    ):
        uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.user_id == uid
            )
        )
        await self.session.flush()

    async def get_active_by_user_id(
        self,
        user_id: str | uuid.UUID,
    ):
        uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == uid,
            RefreshToken.is_revoked == False,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


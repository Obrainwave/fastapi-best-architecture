from app.models.base_models import BaseModel
from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


class RefreshToken(BaseModel):

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )

    token_hash: Mapped[str] = mapped_column(
        String
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
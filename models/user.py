import uuid

import sqlalchemy as sa
from app.models.base_models import BaseModel
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(BaseModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    account: Mapped[str] = mapped_column(String(50), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa.text("false"), nullable=False)

    # Relationships
    # organization = relationship("Organization", back_populates="users")
    # roles = relationship(
    #     "Role",
    #     secondary="user_roles",
    #     viewonly=True,
    # )

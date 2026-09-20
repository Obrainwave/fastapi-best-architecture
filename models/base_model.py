"""
Purpose: Define abstract UUID and timestamp model bases.

This module is the single source of truth for shared SQLAlchemy ORM
building blocks used across all AgroPro models.  Import everything
from here so that models never need to reach into app.database.*
directly.

Exports
-------
Base            – DeclarativeBase subclass that owns the metadata registry.
TimestampMixin  – Adds server-side created_at / updated_at columns.
UUIDMixin       – Adds a uuid.UUID primary key column with a client-side
                  default so rows have an ID before the INSERT is flushed.
SoftDeleteMixin – Optional soft-delete + deleted_at tracking.
BaseModel       – Convenience class = Base + UUIDMixin + TimestampMixin.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """
    Root declarative base for every SQLAlchemy model in AgroPro.

    All models must inherit from this class (directly or via BaseModel).
    It owns the shared MetaData instance, which means all table definitions
    live in one registry — required for Alembic autogenerate and for
    relationship resolution across modules.
    """

    # -----------------------------------------------------------------------
    # Utility helpers available on every model instance
    # -----------------------------------------------------------------------

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Return a plain ``dict`` of column-mapped attributes.

        Parameters
        ----------
        exclude:
            Optional set of column *names* to omit from the result.

        Notes
        -----
        - Only inspects column-mapped attributes (not relationships).
        - ``uuid.UUID`` values are cast to ``str`` for JSON friendliness.
        - ``datetime`` values are returned as-is (use your serialiser's
          ``default`` hook to encode them).
        """
        from sqlalchemy import inspect as sa_inspect

        exclude = exclude or set()
        mapper = sa_inspect(self.__class__)
        result: dict[str, Any] = {}
        for col in mapper.columns:
            if col.key in exclude:
                continue
            val = getattr(self, col.key)
            if isinstance(val, uuid.UUID):
                val = str(val)
            result[col.key] = val
        return result

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """
        Bulk-set column attributes from a mapping.

        Only keys that correspond to actual mapped columns are applied;
        unknown keys are silently ignored, preventing accidental attribute
        pollution.
        """
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(self.__class__)
        column_keys = {col.key for col in mapper.columns}
        for key, value in data.items():
            if key in column_keys:
                setattr(self, key, value)

    def __repr__(self) -> str:
        """
        Developer-friendly repr showing the table name and primary-key value.

        Works for both UUID-keyed and composite-keyed models.
        """
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(self.__class__)
        pk_vals = {
            col.key: getattr(self, col.key)
            for col in mapper.columns
            if col.primary_key
        }
        pairs = ", ".join(f"{k}={v!r}" for k, v in pk_vals.items())
        return f"<{self.__class__.__name__} {pairs}>"

# ---------------------------------------------------------------------------
# Timestamp mixin
# ---------------------------------------------------------------------------

class TimestampMixin:
    """
    Adds ``created_at`` and ``updated_at`` columns to any model.

    Both columns use a PostgreSQL *server-side* default (``NOW()``) so that
    the database clock is always authoritative.  ``updated_at`` is
    automatically refreshed on every UPDATE via ``onupdate``.

    This mixin is designed to be inherited *alongside* ``Base``, not through
    it::

        class MyModel(Base, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=9000,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=9001,
    )

# ---------------------------------------------------------------------------
# UUID primary-key mixin
# ---------------------------------------------------------------------------

class UUIDMixin:
    """
    Adds a ``uuid.UUID`` primary key column named ``id``.

    The default is generated *client-side* (Python) by ``uuid.uuid4`` so
    that:

    1. The ``id`` is available immediately after ``Model(...)`` — before any
       database round-trip.
    2. Batch inserts can reference child rows by ID without a flush.

    The underlying PostgreSQL column type is the native ``UUID`` type
    (16 bytes, indexed efficiently), stored with ``as_uuid=True`` so
    SQLAlchemy returns ``uuid.UUID`` objects instead of strings.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        sort_order=-1,  # Always the first column in DDL output
    )

# ---------------------------------------------------------------------------
# Soft-delete / audit mixin  (opt-in)
# ---------------------------------------------------------------------------

class SoftDeleteMixin:
    """
    Adds non-destructive delete support via a ``deleted_at`` timestamp.

    Usage
    -----
    Inherit this mixin in models that should support soft-delete::

        class MyModel(BaseModel, SoftDeleteMixin):
            __tablename__ = "my_table"

    Query helpers
    -------------
    Call ``instance.soft_delete()`` to mark a row as deleted without
    issuing a SQL ``DELETE``.  Your repository / service layer is
    responsible for filtering out deleted rows (e.g. ``WHERE deleted_at
    IS NULL``) — this mixin intentionally does *not* install a global
    query filter so it stays transparent and composable.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,  # Efficient "active records" filter
        sort_order=9002,
    )

    @property
    def is_deleted(self) -> bool:
        """Return ``True`` when the record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self, now: datetime | None = None) -> None:
        """
        Mark this record as deleted.

        Parameters
        ----------
        now:
            Explicit deletion timestamp.  Defaults to ``datetime.now(utc)``
            when omitted.
        """
        from datetime import timezone

        self.deleted_at = now or datetime.now(tz=timezone.utc)

    def restore(self) -> None:
        """Undo a soft-delete by clearing ``deleted_at``."""
        self.deleted_at = None

# ---------------------------------------------------------------------------
# Convenience composite base
# ---------------------------------------------------------------------------

class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Batteries-included abstract base for standard AgroPro models.

    Provides:
    - A shared ``DeclarativeBase`` registry (``Base``)
    - A native PostgreSQL UUID primary key (``UUIDMixin``)
    - Server-side ``created_at`` / ``updated_at`` timestamps (``TimestampMixin``)
    - ``to_dict()``, ``update_from_dict()``, and ``__repr__()`` helpers

    Standard usage::

        class MyModel(BaseModel):
            __tablename__ = "my_table"

            name: Mapped[str] = mapped_column(String(255))

    With soft-delete::

        class MyModel(BaseModel, SoftDeleteMixin):
            __tablename__ = "my_table"
    """

    __abstract__ = True  # No table is created for this class itself

class OrganizationOwned(BaseModel):
    __abstract__ = True

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    

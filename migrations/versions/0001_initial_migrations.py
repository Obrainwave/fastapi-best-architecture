"""Initial schema migration with tenant and operational tables.

Revision ID: 0001
Revises:
Create Date: 2026-09-04 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def table_exists(bind, table_name):
    """Check if a table exists in the database."""
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(bind, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(bind)
    if not table_exists(bind, table_name):
        return False
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_column_if_not_exists(bind, table_name, column_name, column_def):
    """Add a column to a table if it doesn't already exist."""
    if table_exists(bind, table_name) and not column_exists(
        bind, table_name, column_name
    ):
        op.add_column(table_name, column_def)


def upgrade() -> None:
    """Upgrade database schema."""
    bind = op.get_bind()

    # Create users table
    if not table_exists(bind, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("phone", sa.String(30), nullable=True),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("account", sa.String(20), nullable=False, default="admin"),
            sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )

        # Create subscriptions table
    if not table_exists(bind, "subscriptions"):
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("plan", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("renewal_date", sa.Date(), nullable=True),
            sa.Column("max_users", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )

    # Create audit_logs table
    if not table_exists(bind, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=True),
            sa.Column("action", sa.String(20), nullable=False),
            sa.Column("table_name", sa.String(100), nullable=False),
            sa.Column("record_id", sa.UUID(), nullable=False),
            sa.Column("old_values", sa.JSON(), nullable=True),
            sa.Column("new_values", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )

    # Create notifications table
    if not table_exists(bind, "notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("type", sa.String(20), nullable=True),
            sa.Column("is_read", sa.Boolean(), default=False, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )

    # Create attachments table
    if not table_exists(bind, "attachments"):
        op.create_table(
            "attachments",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("reference_id", sa.UUID(), nullable=False),
            sa.Column("file_name", sa.String(255), nullable=False),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("file_size", sa.BigInteger(), nullable=True),
            sa.Column("uploaded_by", sa.UUID(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        )

    # Create currencies table
    if not table_exists(bind, "currencies"):
        op.create_table(
            "currencies",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("code", sa.String(3), nullable=False, unique=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("symbol", sa.String(10), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )

    # Create exchange_rates table
    if not table_exists(bind, "exchange_rates"):
        op.create_table(
            "exchange_rates",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("currency_id", sa.UUID(), nullable=False),
            sa.Column("rate_date", sa.Date(), nullable=False),
            sa.Column("rate", sa.Numeric(precision=15, scale=6), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["currency_id"], ["currencies.id"]),
        )
        

def downgrade() -> None:
    """Downgrade database schema."""
    bind = op.get_bind()

    # Drop tables in reverse order of creation (respecting foreign keys)
    tables_to_drop = [
        "exchange_rates",
        "currencies",
        "attachments",
        "notifications",
        "audit_logs",
        "subscriptions",
        "users",
    ]

    for table_name in tables_to_drop:
        if table_exists(bind, table_name):
            op.drop_table(table_name)

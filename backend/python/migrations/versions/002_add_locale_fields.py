"""Add locale fields for i18n rollout

Revision ID: 002_add_locale_fields
Revises: 001_initial
Create Date: 2026-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_add_locale_fields"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add locale persistence columns to users and conversations."""
    op.add_column(
        "users",
        sa.Column("preferred_locale", sa.String(length=10), nullable=False, server_default="en-US"),
    )
    op.add_column(
        "conversations",
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="en-US"),
    )

    op.create_index("idx_users_preferred_locale", "users", ["preferred_locale"])
    op.create_index("idx_conversations_locale", "conversations", ["locale"])


def downgrade() -> None:
    """Remove locale persistence columns."""
    op.drop_index("idx_conversations_locale", table_name="conversations")
    op.drop_index("idx_users_preferred_locale", table_name="users")

    op.drop_column("conversations", "locale")
    op.drop_column("users", "preferred_locale")

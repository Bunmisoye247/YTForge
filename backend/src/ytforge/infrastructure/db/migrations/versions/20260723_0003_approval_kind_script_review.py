"""add script_review to approval_kind

Revision ID: 20260723_0003
Revises: 20260723_0002
Create Date: 2026-07-23

"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260723_0003"
down_revision: str | None = "20260723_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE approval_kind ADD VALUE IF NOT EXISTS 'script_review'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; downgrading this one value
    # would require rebuilding the type, which isn't worth it for a single
    # additive approval kind.
    pass

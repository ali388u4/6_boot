"""add chapter files

Revision ID: 20260501_01
Revises: 20260426_01
Create Date: 2026-05-01

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260501_01"
down_revision = "20260426_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chapter_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "chapter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("telegram_file_id", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=500), nullable=True),
        sa.Column("file_type", sa.String(length=32), nullable=False, server_default="document"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("chapter_files")

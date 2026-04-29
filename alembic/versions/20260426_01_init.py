"""init

Revision ID: 20260426_01
Revises: 
Create Date: 2026-04-26

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260426_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("name", name="uq_subjects_name"),
    )

    op.create_table(
        "chapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("subject_id", "title", name="uq_chapters_subject_title"),
    )

    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chapter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("chapter_id", "title", name="uq_topics_chapter_title"),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("solution_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "solving_styles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("style_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("subject_id", name="uq_solving_styles_subject_id"),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("selected_subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("selected_chapter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("selected_topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fsm_state", sa.String(length=128), nullable=True),
        sa.Column("state_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("telegram_user_id", name="uq_user_sessions_telegram_user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("solving_styles")
    op.drop_table("questions")
    op.drop_table("topics")
    op.drop_table("chapters")
    op.drop_table("subjects")

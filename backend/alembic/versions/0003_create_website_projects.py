"""create website_projects table and ai_usage_logs FK

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "website_projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "tech_stack",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "file_tree",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "building", "ready", "deployed", "error", name="project_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_website_projects_user_id", "website_projects", ["user_id"])

    # ai_usage_logs.project_id gains its FK now that the target table exists.
    op.create_foreign_key(
        "fk_ai_usage_logs_project_id",
        "ai_usage_logs",
        "website_projects",
        ["project_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_usage_logs_project_id", "ai_usage_logs", type_="foreignkey")
    op.drop_index("ix_website_projects_user_id", table_name="website_projects")
    op.drop_table("website_projects")
    op.execute("DROP TYPE IF EXISTS project_status")

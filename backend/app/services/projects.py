"""Project persistence. All reads are scoped to the owning user and exclude
soft-deleted rows (CLAUDE.md: never hard-delete, never `SELECT *`)."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import WebsiteProject

logger = logging.getLogger(__name__)


async def create_project(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    description: str,
    tech_stack: dict[str, Any],
) -> WebsiteProject:
    project = WebsiteProject(
        user_id=user_id,
        name=name,
        description=description,
        tech_stack=tech_stack,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    logger.info("Created project %s for user %s", project.id, user_id)
    return project


async def list_projects(db: AsyncSession, user_id: uuid.UUID) -> list[Row[Any]]:
    """Summary rows for a user's live projects (newest first); no `file_tree`."""
    result = await db.execute(
        select(
            WebsiteProject.id,
            WebsiteProject.name,
            WebsiteProject.description,
            WebsiteProject.status,
            WebsiteProject.created_at,
            WebsiteProject.updated_at,
        )
        .where(WebsiteProject.user_id == user_id, WebsiteProject.deleted_at.is_(None))
        .order_by(WebsiteProject.created_at.desc())
    )
    return list(result.all())


async def get_project(
    db: AsyncSession, user_id: uuid.UUID, project_id: uuid.UUID
) -> WebsiteProject | None:
    result = await db.execute(
        select(WebsiteProject).where(
            WebsiteProject.id == project_id,
            WebsiteProject.user_id == user_id,
            WebsiteProject.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete_project(db: AsyncSession, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
    """Mark a project deleted. Returns False if it doesn't exist (or isn't the user's)."""
    project = await get_project(db, user_id, project_id)
    if project is None:
        return False
    project.deleted_at = datetime.now(UTC)
    logger.info("Soft-deleted project %s for user %s", project_id, user_id)
    return True

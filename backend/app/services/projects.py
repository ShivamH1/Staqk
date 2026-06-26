"""Project persistence. All reads are scoped to the owning user and exclude
soft-deleted rows (CLAUDE.md: never hard-delete, never `SELECT *`)."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectStatus, WebsiteProject

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


async def update_project(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    tech_stack: dict[str, Any] | None = None,
) -> WebsiteProject | None:
    """Patch the provided metadata fields. Returns None if the project is absent."""
    project = await get_project(db, user_id, project_id)
    if project is None:
        return None
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if tech_stack is not None:
        project.tech_stack = tech_stack
    return project


async def _get_owned_unscoped(db: AsyncSession, project_id: uuid.UUID) -> WebsiteProject | None:
    """Load a live project by id only — ownership is assumed already checked.

    Used by the pipeline to persist run results into a project it already
    resolved for the connecting user.
    """
    result = await db.execute(
        select(WebsiteProject).where(
            WebsiteProject.id == project_id, WebsiteProject.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def set_status(db: AsyncSession, project_id: uuid.UUID, status: ProjectStatus) -> None:
    """Update only the project's status (e.g. → building at run start)."""
    async with db.begin():
        project = await _get_owned_unscoped(db, project_id)
        if project is not None:
            project.status = status


async def save_run_result(
    db: AsyncSession,
    project_id: uuid.UUID,
    file_tree: dict[str, str],
    status: ProjectStatus,
) -> None:
    """Persist a finished run's file tree and final status."""
    async with db.begin():
        project = await _get_owned_unscoped(db, project_id)
        if project is not None:
            project.file_tree = file_tree
            project.status = status

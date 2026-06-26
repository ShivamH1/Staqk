import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    tech_stack: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Partial metadata update — only provided fields are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    tech_stack: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    tech_stack: dict[str, Any]
    file_tree: dict[str, str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    """List view — omits the (potentially large) `file_tree`."""

    id: uuid.UUID
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

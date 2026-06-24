import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.user import Plan


class UserResponse(BaseModel):
    id: uuid.UUID
    clerk_id: str
    email: str
    credits: int
    plan: Plan
    created_at: datetime

    model_config = {"from_attributes": True}

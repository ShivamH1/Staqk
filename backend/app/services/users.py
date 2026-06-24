import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


async def get_by_clerk_id(clerk_id: str, db: AsyncSession) -> User | None:
    result = await db.execute(
        select(User.id, User.clerk_id, User.email, User.credits, User.plan, User.created_at)
        .where(User.clerk_id == clerk_id)
    )
    row = result.first()
    if row is None:
        return None
    # Re-fetch as ORM object for relationship support
    result2 = await db.execute(select(User).where(User.clerk_id == clerk_id))
    return result2.scalar_one_or_none()


async def create_user(clerk_id: str, email: str, db: AsyncSession) -> User:
    user = User(id=uuid.uuid4(), clerk_id=clerk_id, email=email)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("Created user clerk_id=%s", clerk_id)
    return user

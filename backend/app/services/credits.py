"""Credit ledger operations.

Credits gate every AI operation. The rules (CLAUDE.md / architecture.md):
- Checked *before* an operation starts — too few = `InsufficientCreditsError`,
  nothing runs.
- Deducted *atomically* in one transaction alongside the `AIUsageLog` and a
  `spend` `Transaction`. The user row is locked (`FOR UPDATE`) so concurrent runs
  can't double-spend a balance.
- A failed operation is refunded with a *new* `refund` `Transaction` — never by
  editing or reversing the original spend.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage import AIUsageLog
from app.models.transaction import Transaction, TransactionType
from app.models.user import User

logger = logging.getLogger(__name__)

# Fixed business costs (CLAUDE.md). Not configurable — they are product pricing.
PIPELINE_COST = 5
CHAT_ITERATION_COST = 2


class InsufficientCreditsError(Exception):
    """Raised when a user's balance can't cover an operation. Maps to HTTP 402."""

    def __init__(self, available: int, required: int) -> None:
        self.available = available
        self.required = required
        super().__init__(f"Insufficient credits: have {available}, need {required}")


async def deduct_credits(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    description: str,
    *,
    agent: str = "pipeline",
    provider: str = "multiple",
    model: str = "multiple",
    project_id: uuid.UUID | None = None,
) -> None:
    """Atomically deduct `amount` credits, logging the spend and AI usage.

    Locks the user row, verifies the balance, then in the same transaction
    decrements credits and writes a `spend` `Transaction` + `AIUsageLog`. Raises
    `InsufficientCreditsError` (rolling back, no changes) if the balance is short.
    """
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id).with_for_update())
        user = result.scalar_one_or_none()
        if user is None:
            raise InsufficientCreditsError(0, amount)
        if user.credits < amount:
            raise InsufficientCreditsError(user.credits, amount)

        user.credits -= amount
        db.add(
            Transaction(
                user_id=user_id,
                amount=-amount,
                type=TransactionType.spend,
                description=description,
            )
        )
        db.add(
            AIUsageLog(
                user_id=user_id,
                project_id=project_id,
                agent=agent,
                provider=provider,
                model=model,
                credits_used=amount,
            )
        )
    logger.info("Deducted %d credits from user %s (%s)", amount, user_id, description)


async def refund_credits(
    db: AsyncSession, user_id: uuid.UUID, amount: int, description: str
) -> None:
    """Refund `amount` credits with a new `refund` `Transaction`.

    The original spend is left untouched — the refund is a separate positive
    ledger entry. A no-op (logged) if the user no longer exists.
    """
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id).with_for_update())
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning("Refund skipped — user %s not found", user_id)
            return

        user.credits += amount
        db.add(
            Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.refund,
                description=description,
            )
        )
    logger.info("Refunded %d credits to user %s (%s)", amount, user_id, description)

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
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.exc import IntegrityError
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


async def credit_purchase(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    *,
    reference: str,
    description: str,
) -> bool:
    """Atomically add purchased credits, idempotent on `reference` (payment id).

    Called from the Razorpay webhook after payment is confirmed server-side.
    Returns False (and changes nothing) if this payment was already credited —
    either because a row already exists, or because a concurrent delivery won the
    race (the `reference` unique constraint rejects the duplicate insert).
    """
    try:
        async with db.begin():
            existing = await db.execute(
                select(Transaction.id).where(Transaction.reference == reference)
            )
            if existing.scalar_one_or_none() is not None:
                logger.info("Skipping already-processed payment %s", reference)
                return False

            result = await db.execute(select(User).where(User.id == user_id).with_for_update())
            user = result.scalar_one_or_none()
            if user is None:
                logger.warning("Purchase credit skipped — user %s not found", user_id)
                return False

            user.credits += amount
            db.add(
                Transaction(
                    user_id=user_id,
                    amount=amount,
                    type=TransactionType.purchase,
                    description=description,
                    reference=reference,
                )
            )
    except IntegrityError:
        logger.info("Concurrent delivery already credited payment %s", reference)
        return False

    logger.info("Credited %d credits to user %s (payment %s)", amount, user_id, reference)
    return True


async def list_transactions(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 50
) -> list[Row[Any]]:
    """A user's ledger entries, newest first (capped)."""
    result = await db.execute(
        select(
            Transaction.id,
            Transaction.amount,
            Transaction.type,
            Transaction.description,
            Transaction.created_at,
        )
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.all())

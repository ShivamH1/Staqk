import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionType(StrEnum):
    purchase = "purchase"  # credits added via Stripe
    spend = "spend"  # credits consumed by an AI operation
    refund = "refund"  # credits returned after a failed operation


class Transaction(Base):
    """An immutable credit-ledger entry. Balance changes are never edited in place;
    a refund is a new positive row, never a reversal of the original spend."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    # Signed: positive for purchase/refund, negative for spend.
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    # External payment id (Razorpay) for `purchase` rows — unique so a replayed
    # webhook can't credit twice. NULL for spend/refund (Postgres allows many NULLs).
    reference: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

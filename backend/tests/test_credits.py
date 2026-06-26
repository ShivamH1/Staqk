import uuid
from contextlib import asynccontextmanager
from typing import Any

import pytest

from app.models.transaction import TransactionType
from app.models.user import Plan, User
from app.services.credits import (
    InsufficientCreditsError,
    deduct_credits,
    refund_credits,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _FakeResult:
    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def scalar_one_or_none(self) -> Any:
        return self._obj


class _FakeSession:
    """Minimal AsyncSession stand-in: returns a seeded user and records adds.

    `begin()` is an async context manager that records commit/rollback so tests
    can assert the deduction's atomicity without a real database.
    """

    def __init__(self, user: User | None) -> None:
        self.user = user
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def begin(self) -> Any:
        @asynccontextmanager
        async def _tx() -> Any:
            try:
                yield
            except Exception:
                self.rolled_back = True
                raise
            else:
                self.committed = True

        return _tx()

    async def execute(self, _stmt: Any) -> _FakeResult:
        return _FakeResult(self.user)

    def add(self, obj: Any) -> None:
        self.added.append(obj)


def _user(balance: int) -> User:
    return User(
        id=uuid.uuid4(),
        clerk_id="user_test",
        email="t@staqk.com",
        credits=balance,
        plan=Plan.free,
    )


@pytest.mark.anyio
async def test_deduct_decrements_and_logs() -> None:
    user = _user(100)
    db = _FakeSession(user)

    await deduct_credits(db, user.id, 5, "Full pipeline run")

    assert user.credits == 95
    assert db.committed is True
    txns = [o for o in db.added if type(o).__name__ == "Transaction"]
    usage = [o for o in db.added if type(o).__name__ == "AIUsageLog"]
    assert len(txns) == 1
    assert txns[0].type == TransactionType.spend
    assert txns[0].amount == -5
    assert len(usage) == 1
    assert usage[0].credits_used == 5


@pytest.mark.anyio
async def test_deduct_insufficient_raises_and_changes_nothing() -> None:
    user = _user(3)
    db = _FakeSession(user)

    with pytest.raises(InsufficientCreditsError) as exc:
        await deduct_credits(db, user.id, 5, "Full pipeline run")

    assert exc.value.available == 3
    assert exc.value.required == 5
    assert user.credits == 3  # unchanged
    assert db.added == []
    assert db.rolled_back is True


@pytest.mark.anyio
async def test_deduct_missing_user_raises() -> None:
    db = _FakeSession(None)
    with pytest.raises(InsufficientCreditsError):
        await deduct_credits(db, uuid.uuid4(), 5, "Full pipeline run")


@pytest.mark.anyio
async def test_refund_adds_positive_transaction() -> None:
    user = _user(95)
    db = _FakeSession(user)

    await refund_credits(db, user.id, 5, "Pipeline failed")

    assert user.credits == 100
    txns = [o for o in db.added if type(o).__name__ == "Transaction"]
    assert len(txns) == 1
    assert txns[0].type == TransactionType.refund
    assert txns[0].amount == 5  # positive — a new entry, not a reversal


@pytest.mark.anyio
async def test_refund_missing_user_is_noop() -> None:
    db = _FakeSession(None)
    await refund_credits(db, uuid.uuid4(), 5, "Pipeline failed")
    assert db.added == []

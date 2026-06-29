import hashlib
import hmac
import json
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.models.transaction import Transaction, TransactionType
from app.models.user import Plan, User
from app.services import billing as billing_service
from app.services import credits as credit_service

_USER_ID = uuid.uuid4()
_WEBHOOK_SECRET = "whsec_test"  # noqa: S105 — dummy secret for signing test payloads


def _fake_user() -> User:
    return User(id=_USER_ID, clerk_id="user_test", email="t@staqk.com", credits=100, plan=Plan.free)


def _sign(body: bytes) -> str:
    return hmac.new(_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def authed_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_current_user] = _fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def webhook_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(
        "app.config.settings.razorpay_webhook_secret", _WEBHOOK_SECRET, raising=False
    )

    async def _db() -> AsyncIterator[object]:
        yield object()

    app.dependency_overrides[get_db] = _db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_packs_is_public() -> None:
    with TestClient(app) as client:
        resp = client.get("/billing/packs")
    assert resp.status_code == 200
    ids = {pack["id"] for pack in resp.json()}
    assert ids == set(billing_service.CREDIT_PACKS)
    # Prices are exposed in the smallest currency unit.
    assert all(pack["amount"] > 0 for pack in resp.json())


def test_create_order_requires_auth() -> None:
    with TestClient(app) as client:
        assert client.post("/billing/order", json={"pack_id": "credits_100"}).status_code == 401


def test_create_order_returns_checkout_payload(
    authed_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_create(user_id: uuid.UUID, pack_id: str) -> dict[str, Any]:
        return {"id": "order_abc123", "amount": 79900, "currency": "INR"}

    monkeypatch.setattr(billing_service, "create_order", fake_create)
    monkeypatch.setattr("app.config.settings.razorpay_key_id", "rzp_test_pub", raising=False)

    resp = authed_client.post("/billing/order", json={"pack_id": "credits_100"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_id"] == "order_abc123"
    assert body["amount"] == 79900
    assert body["credits"] == 100
    assert body["pack_id"] == "credits_100"


def test_create_order_unknown_pack_returns_404(
    authed_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_create(user_id: uuid.UUID, pack_id: str) -> dict[str, Any]:
        raise billing_service.UnknownPackError(pack_id)

    monkeypatch.setattr(billing_service, "create_order", fake_create)

    resp = authed_client.post("/billing/order", json={"pack_id": "nope"})
    assert resp.status_code == 404


def test_create_order_unconfigured_returns_503(
    authed_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_create(user_id: uuid.UUID, pack_id: str) -> dict[str, Any]:
        raise billing_service.PaymentError("Razorpay is not configured")

    monkeypatch.setattr(billing_service, "create_order", fake_create)

    resp = authed_client.post("/billing/order", json={"pack_id": "credits_100"})
    assert resp.status_code == 503


def _order_paid_payload(credit_amount: str = "500") -> dict[str, Any]:
    return {
        "event": "order.paid",
        "payload": {
            "order": {
                "entity": {
                    "id": "order_1",
                    "notes": {
                        "user_id": str(_USER_ID),
                        "credits": credit_amount,
                        "pack_id": "credits_500",
                    },
                }
            },
            "payment": {"entity": {"id": "pay_1"}},
        },
    }


def test_webhook_rejects_bad_signature(webhook_client: TestClient) -> None:
    resp = webhook_client.post(
        "/billing/webhook",
        content=b'{"event":"order.paid"}',
        headers={"X-Razorpay-Signature": "deadbeef"},
    )
    assert resp.status_code == 401


def test_webhook_order_paid_credits_user(
    webhook_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded: dict[str, Any] = {}

    async def fake_credit(
        db: Any, user_id: uuid.UUID, amount: int, *, reference: str, description: str
    ) -> bool:
        recorded.update(user_id=user_id, amount=amount, reference=reference)
        return True

    monkeypatch.setattr(credit_service, "credit_purchase", fake_credit)

    body = json.dumps(_order_paid_payload()).encode()
    resp = webhook_client.post(
        "/billing/webhook", content=body, headers={"X-Razorpay-Signature": _sign(body)}
    )
    assert resp.status_code == 200
    assert recorded["user_id"] == _USER_ID
    assert recorded["amount"] == 500
    assert recorded["reference"] == "pay_1"  # payment id, used for idempotency


def test_webhook_ignores_other_events(
    webhook_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    async def fake_credit(*args: Any, **kwargs: Any) -> bool:
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(credit_service, "credit_purchase", fake_credit)

    body = json.dumps({"event": "payment.authorized", "payload": {}}).encode()
    resp = webhook_client.post(
        "/billing/webhook", content=body, headers={"X-Razorpay-Signature": _sign(body)}
    )
    assert resp.status_code == 200
    assert called is False


def test_list_transactions(authed_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        Transaction(
            id=uuid.uuid4(),
            user_id=_USER_ID,
            amount=500,
            type=TransactionType.purchase,
            description="Purchased 500 credits",
            created_at=datetime.now(UTC),
        ),
        Transaction(
            id=uuid.uuid4(),
            user_id=_USER_ID,
            amount=-5,
            type=TransactionType.spend,
            description="Pipeline run",
            created_at=datetime.now(UTC),
        ),
    ]

    async def fake_list(db: Any, user_id: uuid.UUID, limit: int = 50) -> list[Transaction]:
        return rows

    monkeypatch.setattr(credit_service, "list_transactions", fake_list)

    resp = authed_client.get("/billing/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert [t["type"] for t in body] == ["purchase", "spend"]
    assert body[0]["amount"] == 500


def test_list_transactions_requires_auth() -> None:
    with TestClient(app) as client:
        assert client.get("/billing/transactions").status_code == 401

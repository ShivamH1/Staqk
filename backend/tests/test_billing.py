import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.auth import get_current_user
from app.models.user import Plan, User
from app.services import billing as billing_service

_USER_ID = uuid.uuid4()


def _fake_user() -> User:
    return User(id=_USER_ID, clerk_id="user_test", email="t@staqk.com", credits=100, plan=Plan.free)


@pytest.fixture
def authed_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_current_user] = _fake_user
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

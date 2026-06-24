import os
import uuid

import pytest

os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("CLERK_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/staqk")
os.environ.setdefault("DATABASE_URL_DIRECT", "postgresql://u:p@localhost/staqk")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-dummy")
os.environ.setdefault("E2B_API_KEY", "e2b_dummy")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models.user import Plan, User  # noqa: E402


def _fake_user() -> User:
    return User(
        id=uuid.uuid4(),
        clerk_id="user_test",
        email="test@staqk.com",
        credits=100,
        plan=Plan.free,
    )


def test_ws_rejects_missing_token() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ai/stream/proj-1") as ws:  # noqa: SIM117
        # Server should close immediately with a policy-violation code.
        with pytest.raises(Exception):  # noqa: B017, PT011
            ws.receive_json()


def test_ws_streams_full_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    # Bypass real Clerk/DB auth — return a fake user for any token.
    async def fake_verify(token: str, db: object) -> User:
        return _fake_user()

    monkeypatch.setattr("app.routers.ai.verify_token_get_user", fake_verify)

    client = TestClient(app)
    with client.websocket_connect("/ai/stream/proj-1?token=abc") as ws:
        ws.send_json({"user_message": "build a todo app", "tech_stack": {}})

        events: list[dict] = []
        while True:
            msg = ws.receive_json()
            events.append(msg)
            if msg["type"] in ("pipeline_complete", "pipeline_error"):
                break

    types = [e["type"] for e in events]
    assert "pipeline_complete" in types
    assert types[-1] == "pipeline_complete"

    started = {e["agent"] for e in events if e["type"] == "agent_start"}
    completed = {e["agent"] for e in events if e["type"] == "agent_complete"}
    assert started == {"plan", "code", "test", "security", "deploy"}
    assert completed == {"plan", "code", "test", "security", "deploy"}

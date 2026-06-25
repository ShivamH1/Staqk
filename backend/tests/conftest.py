import json
import os
from typing import Any

import pytest

# Set required settings before any `app` import triggers Pydantic Settings.
os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("CLERK_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/staqk")
os.environ.setdefault("DATABASE_URL_DIRECT", "postgresql://u:p@localhost/staqk")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-dummy")
os.environ.setdefault("E2B_API_KEY", "e2b_dummy")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


_FAKE_PLAN = {
    "components": ["Home"],
    "routes": [{"path": "/", "component": "Home", "auth": False}],
    "db_schema": [],
    "api_endpoints": [],
    "notes": "fake plan from test",
}


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeModel:
    def __init__(self, content: str) -> None:
        self._content = content

    async def ainvoke(self, _messages: object) -> _FakeResponse:
        return _FakeResponse(self._content)


@pytest.fixture(autouse=True)
def mock_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace real LLM construction with a fake that returns a valid plan JSON.

    Keeps the full-pipeline and WS tests offline. Individual tests can override
    by patching `app.agents.models.get_chat_model` again.
    """

    def fake_get_chat_model(_agent: str) -> _FakeModel:
        return _FakeModel(json.dumps(_FAKE_PLAN))

    monkeypatch.setattr("app.agents.models.get_chat_model", fake_get_chat_model)


def fake_model_returning(content: str | dict[str, Any]) -> _FakeModel:
    """Helper for tests that want a specific model response."""
    payload = content if isinstance(content, str) else json.dumps(content)
    return _FakeModel(payload)

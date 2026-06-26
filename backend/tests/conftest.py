import json
import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
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

_FAKE_FILE_TREE = {
    "package.json": '{"name":"app","scripts":{"build":"next build"}}',
    "app/page.tsx": "export default function Page() { return null }",
}

_FAKE_TEST_TREE = {
    "app/page.test.tsx": "import { test } from 'vitest'\ntest('renders', () => {})",
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
    """Replace real LLM construction with fakes that return valid agent output.

    The Plan agent gets a plan JSON; the Code agent gets a file-tree JSON; the
    Test agent gets a test-tree JSON. Keeps the full-pipeline and WS tests
    offline. Individual tests can override by patching
    `app.agents.models.get_chat_model` again.
    """

    def fake_get_chat_model(agent: str) -> _FakeModel:
        if agent == "code":
            return _FakeModel(json.dumps(_FAKE_FILE_TREE))
        if agent == "test":
            return _FakeModel(json.dumps(_FAKE_TEST_TREE))
        return _FakeModel(json.dumps(_FAKE_PLAN))

    monkeypatch.setattr("app.agents.models.get_chat_model", fake_get_chat_model)


def fake_model_returning(content: str | dict[str, Any]) -> _FakeModel:
    """Helper for tests that want a specific model response."""
    payload = content if isinstance(content, str) else json.dumps(content)
    return _FakeModel(payload)


class _FakeSandbox:
    """Stand-in for the E2B sandbox: records writes, returns canned exit codes."""

    def __init__(self, exit_codes: Sequence[int]) -> None:
        self._exit_codes = list(exit_codes)
        self.written: dict[str, str] = {}

    async def write_files(self, files: dict[str, str]) -> None:
        self.written.update(files)

    async def read_file(self, path: str) -> str:
        return self.written.get(path, "")

    async def run(self, cmd: str, timeout: float = 240) -> Any:  # noqa: ASYNC109
        from app.sandbox.e2b import CommandOutcome

        code = self._exit_codes.pop(0) if self._exit_codes else 0
        stderr = "" if code == 0 else f"command failed: {cmd}"
        return CommandOutcome(exit_code=code, stdout="output", stderr=stderr)


def fake_sandbox_session(*exit_codes: int) -> Any:
    """Build a no-arg callable yielding a `_FakeSandbox` with the given run results."""

    @asynccontextmanager
    async def _session() -> AsyncIterator[_FakeSandbox]:
        yield _FakeSandbox(exit_codes)

    return _session


@pytest.fixture(autouse=True)
def mock_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the Code + Test agents' sandboxes so they succeed without hitting E2B."""
    monkeypatch.setattr("app.agents.code_agent.sandbox_session", fake_sandbox_session())
    monkeypatch.setattr("app.agents.test_agent.sandbox_session", fake_sandbox_session())

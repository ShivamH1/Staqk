import os
from typing import Any

import pytest

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


@pytest.mark.anyio
async def test_pipeline_streams_all_agents() -> None:
    from app.agents.graph import pipeline
    from app.agents.state import AgentState

    state: AgentState = {
        "project_id": "test-project",
        "user_message": "build a todo app",
        "tech_stack": {"framework": "next"},
        "existing_file_tree": {},
        "retry_count": 0,
    }

    events: list[dict[str, Any]] = []
    async for event in pipeline.astream(state, stream_mode="custom"):
        events.append(event)

    started = {e["agent"] for e in events if e["type"] == "agent_start"}
    completed = {e["agent"] for e in events if e["type"] == "agent_complete"}

    assert started == {"plan", "code", "test", "security", "deploy"}
    assert completed == {"plan", "code", "test", "security", "deploy"}


@pytest.mark.anyio
async def test_pipeline_reaches_deploy_with_url() -> None:
    from app.agents.graph import pipeline
    from app.agents.state import AgentState

    state: AgentState = {
        "project_id": "test-project",
        "user_message": "build a todo app",
        "tech_stack": {},
        "existing_file_tree": {},
        "retry_count": 0,
    }

    final = await pipeline.ainvoke(state)
    assert final.get("deployment_url")
    assert final.get("security_cleared") is True
    assert final.get("tests_passed") is True

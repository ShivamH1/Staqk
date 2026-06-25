import pytest

from app.agents.plan_agent import parse_plan_json, plan_node
from app.agents.state import AgentState
from tests.conftest import fake_model_returning


def test_parse_plan_json_plain() -> None:
    plan = parse_plan_json('{"components": ["Home"], "notes": "x"}')
    assert plan["components"] == ["Home"]


def test_parse_plan_json_strips_code_fence() -> None:
    fenced = '```json\n{"components": [], "notes": "y"}\n```'
    plan = parse_plan_json(fenced)
    assert plan["notes"] == "y"


@pytest.mark.anyio
async def test_plan_node_returns_plan() -> None:
    state: AgentState = {"user_message": "build a todo app", "tech_stack": {}}
    result = await plan_node(state)
    assert "plan" in result
    assert result["plan"]["components"] == ["Home"]
    assert "error" not in result


@pytest.mark.anyio
async def test_plan_node_handles_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.models.get_chat_model",
        lambda _agent: fake_model_returning("not json at all"),
    )
    state: AgentState = {"user_message": "build a todo app", "tech_stack": {}}
    result = await plan_node(state)
    assert "error" in result
    assert "plan" not in result

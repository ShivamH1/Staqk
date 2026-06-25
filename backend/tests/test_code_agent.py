import pytest

from app.agents.code_agent import code_node, parse_file_tree
from app.agents.state import MAX_CODE_RETRIES, AgentState
from tests.conftest import fake_model_returning, fake_sandbox_session


def test_parse_file_tree_plain() -> None:
    tree = parse_file_tree('{"app/page.tsx": "x", "package.json": "{}"}')
    assert tree["app/page.tsx"] == "x"
    assert set(tree) == {"app/page.tsx", "package.json"}


def test_parse_file_tree_strips_code_fence() -> None:
    tree = parse_file_tree('```json\n{"a.ts": "y"}\n```')
    assert tree["a.ts"] == "y"


def test_parse_file_tree_rejects_non_object() -> None:
    with pytest.raises(ValueError):
        parse_file_tree('["not", "an", "object"]')


def test_parse_file_tree_serialises_object_content() -> None:
    # Models often emit config files (package.json) as nested objects.
    tree = parse_file_tree('{"package.json": {"name": "app", "version": "1.0.0"}}')
    assert '"name": "app"' in tree["package.json"]


def test_parse_file_tree_rejects_non_string_content() -> None:
    with pytest.raises(ValueError):
        parse_file_tree('{"a.ts": 123}')


@pytest.mark.anyio
async def test_code_node_success() -> None:
    state: AgentState = {"plan": {}, "tech_stack": {}, "retry_count": 0}
    result = await code_node(state)
    assert result["build_success"] is True
    assert "package.json" in result["file_tree"]
    assert result.get("error") is None


@pytest.mark.anyio
async def test_code_node_build_failure_requests_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    # npm install ok (0), npm run build fails (1)
    monkeypatch.setattr("app.agents.code_agent.sandbox_session", fake_sandbox_session(0, 1))
    state: AgentState = {"plan": {}, "tech_stack": {}, "retry_count": 0}
    result = await code_node(state)
    assert result["build_success"] is False
    assert result["retry_count"] == 1
    assert "npm run build failed" in result["build_error"]
    assert "error" not in result


@pytest.mark.anyio
async def test_code_node_halts_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.agents.code_agent.sandbox_session", fake_sandbox_session(1))
    state: AgentState = {"plan": {}, "tech_stack": {}, "retry_count": MAX_CODE_RETRIES}
    result = await code_node(state)
    assert result["build_success"] is False
    assert result["error"]
    assert "retry_count" not in result


@pytest.mark.anyio
async def test_code_node_invalid_output_sets_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.models.get_chat_model",
        lambda _agent: fake_model_returning("not json"),
    )
    state: AgentState = {"plan": {}, "tech_stack": {}, "retry_count": 0}
    result = await code_node(state)
    assert result["build_success"] is False
    assert "error" in result

import pytest

from app.agents.state import MAX_CODE_RETRIES, AgentState
from app.agents.test_agent import _parse_results
from app.agents.test_agent import test_node as run_test_node
from tests.conftest import fake_model_returning, fake_sandbox_session

_STATE: AgentState = {
    "plan": {},
    "tech_stack": {},
    "file_tree": {"app/page.tsx": "x"},
    "retry_count": 0,
}


def test_parse_results_reads_counts() -> None:
    results = _parse_results({"a.test.ts": "x"}, "Tests  3 passed | 1 failed (4)", passed=False)
    assert results == [{"file": "suite", "passed": 3, "failed": 1}]


def test_parse_results_falls_back_when_unparseable() -> None:
    results = _parse_results({"a.test.ts": "x"}, "no summary here", passed=True)
    assert results == [{"file": "suite", "passed": 1, "failed": 0}]


@pytest.mark.anyio
async def test_test_node_passes() -> None:
    result = await run_test_node(dict(_STATE))
    assert result["tests_passed"] is True
    assert result.get("error") is None


@pytest.mark.anyio
async def test_test_node_failure_requests_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    # npm install ok (0), vitest fails (1)
    monkeypatch.setattr("app.agents.test_agent.sandbox_session", fake_sandbox_session(0, 1))
    result = await run_test_node(dict(_STATE))
    assert result["tests_passed"] is False
    assert result["retry_count"] == 1
    assert result["test_failures"]
    assert "error" not in result


@pytest.mark.anyio
async def test_test_node_halts_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.agents.test_agent.sandbox_session", fake_sandbox_session(0, 1))
    state = dict(_STATE)
    state["retry_count"] = MAX_CODE_RETRIES
    result = await run_test_node(state)
    assert result["tests_passed"] is False
    assert result["error"]
    assert "retry_count" not in result


@pytest.mark.anyio
async def test_test_node_invalid_output_sets_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.models.get_chat_model",
        lambda _agent: fake_model_returning("not json"),
    )
    result = await run_test_node(dict(_STATE))
    assert result["tests_passed"] is False
    assert "error" in result

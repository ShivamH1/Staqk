import json

import pytest

from app.agents.security_agent import parse_findings, security_node
from app.agents.state import AgentState
from tests.conftest import fake_semgrep_session

_STATE: AgentState = {
    "plan": {},
    "tech_stack": {},
    "file_tree": {"app/page.tsx": "x"},
    "retry_count": 0,
}


def _result(check_id: str, *, cli: str = "WARNING", impact: str | None = None) -> dict:
    metadata: dict[str, str] = {}
    if impact is not None:
        metadata["impact"] = impact
    return {
        "check_id": check_id,
        "path": "app/page.tsx",
        "start": {"line": 3},
        "extra": {"severity": cli, "message": "issue", "metadata": metadata},
    }


def _scan(*results: dict) -> str:
    return json.dumps({"results": list(results)})


def test_parse_findings_normalises_severity() -> None:
    findings = parse_findings(
        _scan(
            _result("rules.error", cli="ERROR"),
            _result("rules.warn", cli="WARNING"),
            _result("rules.info", cli="INFO"),
            _result("rules.crit", cli="ERROR", impact="CRITICAL"),
        )
    )
    severities = [f["severity"] for f in findings]
    assert severities == ["high", "medium", "low", "critical"]
    assert findings[0]["rule"] == "rules.error"
    assert findings[0]["file"] == "app/page.tsx"
    assert findings[0]["line"] == 3


def test_parse_findings_rejects_non_semgrep_output() -> None:
    with pytest.raises(ValueError):
        parse_findings('{"not": "semgrep"}')


@pytest.mark.anyio
async def test_security_node_clean_scan_clears() -> None:
    # Default autouse mock returns an empty Semgrep scan.
    result = await security_node(dict(_STATE))
    assert result["security_cleared"] is True
    assert result["security_findings"] == []
    assert result.get("error") is None


@pytest.mark.anyio
async def test_security_node_halts_on_critical(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.security_agent.sandbox_session",
        fake_semgrep_session(_scan(_result("rules.crit", cli="ERROR", impact="CRITICAL"))),
    )
    result = await security_node(dict(_STATE))
    assert result["security_cleared"] is False
    assert result["error"]
    assert result["security_findings"][0]["severity"] == "critical"


@pytest.mark.anyio
async def test_security_node_autofixes_then_rescans_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    # First scan: a fixable (medium) finding. Re-scan after the fix: clean.
    monkeypatch.setattr(
        "app.agents.security_agent.sandbox_session",
        fake_semgrep_session(_scan(_result("rules.warn", cli="WARNING")), _scan()),
    )
    result = await security_node(dict(_STATE))
    assert result["security_cleared"] is True
    assert result["security_findings"] == []
    # The corrected tree from the fix model is propagated back to state.
    assert result["file_tree"]


@pytest.mark.anyio
async def test_security_node_autofix_then_critical_halts(monkeypatch: pytest.MonkeyPatch) -> None:
    # A medium finding gets fixed, but the re-scan surfaces a critical one.
    monkeypatch.setattr(
        "app.agents.security_agent.sandbox_session",
        fake_semgrep_session(
            _scan(_result("rules.warn", cli="WARNING")),
            _scan(_result("rules.crit", cli="ERROR", impact="CRITICAL")),
        ),
    )
    result = await security_node(dict(_STATE))
    assert result["security_cleared"] is False
    assert result["error"]
    assert result["file_tree"]


@pytest.mark.anyio
async def test_security_node_scan_failure_sets_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.security_agent.sandbox_session",
        fake_semgrep_session("not json at all"),
    )
    result = await security_node(dict(_STATE))
    assert result["security_cleared"] is False
    assert result["error"]


@pytest.mark.anyio
async def test_security_node_low_findings_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.security_agent.sandbox_session",
        fake_semgrep_session(_scan(_result("rules.info", cli="INFO"))),
    )
    result = await security_node(dict(_STATE))
    assert result["security_cleared"] is True
    assert result["security_findings"][0]["severity"] == "low"

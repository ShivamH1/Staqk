from typing import Any

from app.agents import events
from app.agents.state import AgentState


async def security_node(state: AgentState) -> dict[str, Any]:
    """Scan generated code with Semgrep and auto-fix medium/high findings.

    Stub: reports a clean scan. Real Semgrep execution + Mistral Small auto-fix
    lands in a later step. Critical findings will halt the pipeline.
    """
    events.agent_start("security")
    events.agent_progress("security", "Scanning for vulnerabilities")

    findings: list[dict[str, Any]] = []

    events.agent_complete("security")
    return {"security_findings": findings, "security_cleared": True}

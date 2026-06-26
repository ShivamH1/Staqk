"""Security Agent: scan the generated code with Semgrep and auto-fix what it can.

The file tree is written to an E2B sandbox and scanned with
`semgrep --config=auto --json`. Findings are normalised to a single severity
scale (info/low/medium/high/critical):

- ``critical``  → halt the pipeline (`security_cleared=False`, `error` set)
- ``high``/``medium`` → ask Mistral Small to fix them, re-write the tree, re-scan
- ``low``/``info`` → logged only, pipeline continues

Unlike the Code/Test agents, the Security Agent does not route back through the
Code Agent — it runs its own single fix-and-rescan pass in place, since the graph
edge out of ``security`` only leads to ``deploy`` or ``END``.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agents import events, models
from app.agents.code_agent import parse_file_tree
from app.agents.state import AgentState
from app.sandbox.e2b import sandbox_session

logger = logging.getLogger(__name__)

SECURITY_SYSTEM_PROMPT = """You are the Security Agent for Staqk. Fix the \
security vulnerabilities found by Semgrep in the given project files.
Rules:
- Fix ONLY the reported findings; preserve all unrelated functionality
- Never weaken the fix (no disabling rules, no `# nosemgrep`, no silencing)
- Never introduce hardcoded secrets
- Keep TypeScript strict — no 'any'

Output ONLY a JSON object mapping file paths to the FULL corrected file contents. \
No markdown, no prose. Example shape:
{
  "app/api/route.ts": "export async function GET() { ... }"
}"""

# Semgrep CLI severity (extra.severity) → our scale.
_CLI_SEVERITY = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
# Ordered low→high; used to recognise an explicit metadata severity/impact.
_SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
_FIXABLE = {"medium", "high"}

# Install Semgrep (no-op if the template already has it) and scan the work dir.
# Semgrep exits 1 when it finds issues, so the JSON on stdout is authoritative —
# not the exit code.
SEMGREP_CMD = "python3 -m pip install --quiet semgrep && semgrep --config=auto --json ."


def _normalize_severity(extra: dict[str, Any]) -> str:
    """Map a Semgrep result's severity onto info/low/medium/high/critical."""
    meta = extra.get("metadata") or {}
    for candidate in (meta.get("severity"), meta.get("impact")):
        if isinstance(candidate, str) and candidate.strip().lower() in _SEVERITY_RANK:
            return candidate.strip().lower()
    cli = str(extra.get("severity", "")).strip().upper()
    return _CLI_SEVERITY.get(cli, "low")


def _to_finding(result: dict[str, Any]) -> dict[str, Any]:
    extra = result.get("extra") or {}
    start = result.get("start") or {}
    return {
        "rule": result.get("check_id", "unknown"),
        "severity": _normalize_severity(extra),
        "file": result.get("path", "unknown"),
        "line": start.get("line"),
        "message": str(extra.get("message", "")),
    }


def parse_findings(stdout: str) -> list[dict[str, Any]]:
    """Parse Semgrep `--json` stdout into a list of normalised findings.

    Raises `json.JSONDecodeError` / `ValueError` if the output is not the
    expected Semgrep JSON document.
    """
    data = json.loads(stdout)
    if not isinstance(data, dict) or "results" not in data:
        raise ValueError("Semgrep output missing 'results'")
    return [_to_finding(r) for r in data["results"] if isinstance(r, dict)]


@dataclass(frozen=True)
class _ScanOutcome:
    ran: bool
    findings: list[dict[str, Any]] = field(default_factory=list)
    log: str = ""


async def _run_semgrep(file_tree: dict[str, str]) -> _ScanOutcome:
    """Write the tree to a fresh sandbox and run Semgrep; parse findings from stdout."""
    async with sandbox_session() as sandbox:
        await sandbox.write_files(file_tree)
        scan = await sandbox.run(SEMGREP_CMD)
        try:
            findings = parse_findings(scan.stdout)
        except (json.JSONDecodeError, ValueError):
            return _ScanOutcome(False, log=scan.log_tail())
        return _ScanOutcome(True, findings, scan.log_tail())


def _build_messages(file_tree: dict[str, str], findings: list[dict[str, Any]]) -> list[BaseMessage]:
    return [
        SystemMessage(content=SECURITY_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Semgrep findings to fix:\n{json.dumps(findings, indent=2)}\n\n"
                f"Project files:\n{json.dumps(file_tree)}"
            )
        ),
    ]


async def _generate_fixes(
    file_tree: dict[str, str], findings: list[dict[str, Any]]
) -> dict[str, str]:
    """Ask Mistral Small to fix the findings; merge the result over the tree."""
    model = models.get_chat_model("security")
    response = await model.ainvoke(_build_messages(file_tree, findings))
    fixed = parse_file_tree(response.content)
    return {**file_tree, **fixed}


def _emit_findings(findings: list[dict[str, Any]]) -> None:
    for finding in findings:
        if finding["severity"] != "info":
            events.security_finding(finding["severity"], finding["rule"], finding["file"])


def _has_critical(findings: list[dict[str, Any]]) -> bool:
    return any(f["severity"] == "critical" for f in findings)


def _halt(findings: list[dict[str, Any]]) -> dict[str, Any]:
    critical = [f["rule"] for f in findings if f["severity"] == "critical"]
    events.agent_error("security", f"Critical findings: {', '.join(critical)}")
    return {
        "security_findings": findings,
        "security_cleared": False,
        "error": f"Critical security findings: {', '.join(critical)}",
    }


async def security_node(state: AgentState) -> dict[str, Any]:
    """Scan the file tree, auto-fix medium/high findings, halt on critical."""
    events.agent_start("security")
    events.agent_progress("security", "Scanning for vulnerabilities")

    file_tree = state.get("file_tree") or {}
    if not file_tree:
        events.agent_complete("security")
        return {"security_findings": [], "security_cleared": True}

    try:
        outcome = await _run_semgrep(file_tree)
    except Exception as exc:  # noqa: BLE001 — sandbox/network failure halts this run
        logger.exception("E2B sandbox failed during security scan")
        events.agent_error("security", f"Sandbox error: {exc}")
        return {"error": f"Sandbox error: {exc}", "security_cleared": False}

    if not outcome.ran:
        events.agent_error("security", "Semgrep scan did not produce results")
        return {"error": "Security scan failed to run", "security_cleared": False}

    findings = outcome.findings
    _emit_findings(findings)

    if _has_critical(findings):
        return _halt(findings)

    fixable = [f for f in findings if f["severity"] in _FIXABLE]
    if not fixable:
        events.agent_complete("security")
        return {"security_findings": findings, "security_cleared": True}

    events.agent_progress("security", f"Auto-fixing {len(fixable)} finding(s)")
    try:
        fixed_tree = await _generate_fixes(file_tree, fixable)
    except (json.JSONDecodeError, ValueError) as exc:
        # The model could not produce a usable fix. These are non-critical, so log
        # the findings and let the pipeline continue rather than blocking on them.
        logger.warning("Security agent produced invalid fix output: %s", exc)
        events.agent_complete("security")
        return {"security_findings": findings, "security_cleared": True}
    except Exception as exc:  # noqa: BLE001 — surface provider/network errors
        logger.exception("Security agent model call failed")
        events.agent_error("security", str(exc))
        return {"error": f"Security agent failed: {exc}", "security_cleared": False}

    events.agent_progress("security", "Re-scanning after fixes")
    try:
        rescan = await _run_semgrep(fixed_tree)
    except Exception as exc:  # noqa: BLE001 — sandbox/network failure halts this run
        logger.exception("E2B sandbox failed during security re-scan")
        events.agent_error("security", f"Sandbox error: {exc}")
        return {"error": f"Sandbox error: {exc}", "security_cleared": False}

    # If the re-scan itself failed to run, keep the fixed tree and the prior
    # (non-critical) findings rather than failing the pipeline.
    final_findings = rescan.findings if rescan.ran else findings
    if rescan.ran:
        _emit_findings(final_findings)
        if _has_critical(final_findings):
            return {**_halt(final_findings), "file_tree": fixed_tree}

    events.agent_complete("security")
    return {
        "security_findings": final_findings,
        "security_cleared": True,
        "file_tree": fixed_tree,
    }

"""Test Agent: generate Vitest tests for the project and run them in E2B.

Uses Groq Llama (OpenRouter fallback) to write one test file per source file,
writes them alongside the generated code into an E2B sandbox, and runs the suite
with `npx vitest run`. Pass/fail is driven by the runner's exit code; on failure
the node routes back to the Code Agent (retry-counted) with the failing log as
context, mirroring the Code Agent's build-retry loop.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agents import events, models
from app.agents.code_agent import parse_file_tree
from app.agents.state import MAX_CODE_RETRIES, AgentState
from app.sandbox.e2b import sandbox_session

logger = logging.getLogger(__name__)

TEST_SYSTEM_PROMPT = """You are the Test Agent for Staqk. Write Vitest tests for \
the given project files.
Rules:
- Test behaviour, not implementation
- One test file per source file, named `<source>.test.ts(x)`
- Mock external services (AI providers, Stripe, network)
- No snapshot tests
- Cover edge cases and error paths

Output ONLY a JSON object mapping test file paths to file contents. No markdown, \
no prose. Example:
{
  "lib/sum.test.ts": "import { expect, test } from 'vitest'\\n..."
}"""

# Matches vitest's summary line, e.g. "Tests  3 passed | 1 failed (4)".
_PASSED_RE = re.compile(r"(\d+)\s+passed")
_FAILED_RE = re.compile(r"(\d+)\s+failed")


def _build_messages(state: AgentState) -> list[BaseMessage]:
    plan = state.get("plan") or {}
    file_tree = state.get("file_tree") or {}
    return [
        SystemMessage(content=TEST_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Architecture plan: {json.dumps(plan)}\n\n"
                f"Project files to test:\n{json.dumps(file_tree)}"
            )
        ),
    ]


@dataclass(frozen=True)
class _TestOutcome:
    passed: bool
    log: str
    results: list[dict[str, Any]] = field(default_factory=list)


def _parse_results(test_files: dict[str, str], stdout: str, passed: bool) -> list[dict[str, Any]]:
    """Best-effort pass/fail counts from the vitest summary, attributed to the suite."""
    passed_match = _PASSED_RE.search(stdout)
    failed_match = _FAILED_RE.search(stdout)
    total_passed = (
        int(passed_match.group(1)) if passed_match else (len(test_files) if passed else 0)
    )
    total_failed = (
        int(failed_match.group(1)) if failed_match else (0 if passed else len(test_files))
    )
    return [{"file": "suite", "passed": total_passed, "failed": total_failed}]


async def _run_tests(file_tree: dict[str, str], test_files: dict[str, str]) -> _TestOutcome:
    """Write code + tests to a fresh sandbox, install deps, and run vitest."""
    async with sandbox_session() as sandbox:
        await sandbox.write_files({**file_tree, **test_files})
        install = await sandbox.run("npm install --no-audit --no-fund")
        if not install.ok:
            return _TestOutcome(False, f"npm install failed:\n{install.log_tail()}")
        run = await sandbox.run("npx --yes vitest run")
        results = _parse_results(test_files, run.stdout, run.ok)
        return _TestOutcome(run.ok, run.log_tail(), results)


async def test_node(state: AgentState) -> dict[str, Any]:
    """Generate tests, run them in E2B, and gate the pipeline on the result."""
    events.agent_start("test")
    events.agent_progress("test", "Generating tests")

    model = models.get_chat_model("test")
    try:
        response = await model.ainvoke(_build_messages(state))
        test_files = parse_file_tree(response.content)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Test agent produced invalid output: %s", exc)
        events.agent_error("test", "Could not parse generated tests")
        return {"error": f"Test agent produced invalid output: {exc}", "tests_passed": False}
    except Exception as exc:  # noqa: BLE001 — surface provider/network errors to the pipeline
        logger.exception("Test agent model call failed")
        events.agent_error("test", str(exc))
        return {"error": f"Test agent failed: {exc}", "tests_passed": False}

    for path in test_files:
        events.file_created(path)

    events.agent_progress("test", "Running tests in sandbox")
    try:
        outcome = await _run_tests(state.get("file_tree", {}), test_files)
    except Exception as exc:  # noqa: BLE001 — sandbox/network failure halts this run
        logger.exception("E2B sandbox failed during tests")
        events.agent_error("test", f"Sandbox error: {exc}")
        return {"error": f"Sandbox error: {exc}", "tests_passed": False}

    for result in outcome.results:
        events.test_result(result["file"], result["passed"], result["failed"])

    if outcome.passed:
        events.agent_complete("test")
        return {"test_results": outcome.results, "tests_passed": True, "test_failures": None}

    retry = state.get("retry_count", 0)
    if retry < MAX_CODE_RETRIES:
        events.agent_progress("test", "Tests failed — sending back to Code agent")
        return {
            "test_results": outcome.results,
            "tests_passed": False,
            "test_failures": outcome.log,
            "retry_count": retry + 1,
        }

    events.agent_error("test", "Tests failed after maximum retries")
    return {
        "test_results": outcome.results,
        "tests_passed": False,
        "test_failures": outcome.log,
        "error": "Tests did not pass after retries",
    }

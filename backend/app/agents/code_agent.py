"""Code Agent: generate the project file tree and verify it builds in E2B.

Generation uses Mistral Large (OpenRouter fallback). The generated `{path:
content}` tree is written to an E2B sandbox and verified with
`npm install && npm run build`. On build failure the node returns
`build_success=False` with the build log as `build_error`; the graph routes back
here (up to MAX_CODE_RETRIES) so the model can fix its own output, then halts.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agents import events, models
from app.agents.state import MAX_CODE_RETRIES, AgentState
from app.sandbox.e2b import sandbox_session

logger = logging.getLogger(__name__)

CODE_SYSTEM_PROMPT = """You are the Code Agent for Staqk. Generate complete, \
production-ready files for the project described by the plan.
Rules:
- Every file must be complete — no placeholders, no TODOs
- Never include hardcoded secrets or API keys
- TypeScript strict mode — no 'any'
- If iterating on existing code, preserve unrelated functionality
- The project MUST build with `npm install && npm run build`

Output ONLY a JSON object mapping file paths to file contents. No markdown, no \
prose. Example shape:
{
  "package.json": "{ ... }",
  "app/page.tsx": "export default function Page() { return null }"
}"""


def _content_to_text(content: str | list[str | dict[str, Any]]) -> str:
    """Normalise message content (str or content-block list) to plain text."""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and "text" in block:
            parts.append(str(block["text"]))
    return "".join(parts)


def parse_file_tree(content: str | list[str | dict[str, Any]]) -> dict[str, str]:
    """Extract a {path: content} file map from an LLM response.

    Tolerates ```json fences. Models often emit JSON config files (package.json,
    tsconfig.json) as nested objects rather than strings — those are serialised
    back to JSON text. Numeric/boolean/null contents are rejected as invalid.
    """
    text = _content_to_text(content).strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object mapping file paths to contents")
    file_tree: dict[str, str] = {}
    for path, value in parsed.items():
        if isinstance(value, str):
            file_tree[str(path)] = value
        elif isinstance(value, (dict, list)):
            file_tree[str(path)] = json.dumps(value, indent=2)
        else:
            raise ValueError(f"File content for {path!r} must be a string or JSON object")
    return file_tree


def _build_messages(state: AgentState) -> list[BaseMessage]:
    plan = state.get("plan") or {}
    tech = state.get("tech_stack") or {}
    parts = [
        f"Tech stack: {json.dumps(tech)}",
        f"Architecture plan: {json.dumps(plan)}",
    ]

    build_error = state.get("build_error")
    test_failures = state.get("test_failures")
    if build_error or test_failures:
        previous = state.get("file_tree") or state.get("existing_file_tree") or {}
        if build_error:
            parts.append(
                "The previous attempt FAILED to build. Fix the errors and return the "
                "FULL corrected file tree.\n\nBuild error:\n" + build_error
            )
        if test_failures:
            parts.append(
                "The previous attempt built but FAILED its tests. Fix the code (not the "
                "tests) and return the FULL corrected file tree.\n\nTest failures:\n"
                + test_failures
            )
        if previous:
            parts.append("Previous files:\n" + json.dumps(previous))

    return [
        SystemMessage(content=CODE_SYSTEM_PROMPT),
        HumanMessage(content="\n\n".join(parts)),
    ]


@dataclass(frozen=True)
class _BuildResult:
    ok: bool
    log: str


async def _verify_build(file_tree: dict[str, str]) -> _BuildResult:
    """Write files to a fresh sandbox and run install + build."""
    async with sandbox_session() as sandbox:
        await sandbox.write_files(file_tree)
        install = await sandbox.run("npm install --no-audit --no-fund")
        if not install.ok:
            return _BuildResult(False, f"npm install failed:\n{install.log_tail()}")
        build = await sandbox.run("npm run build")
        if not build.ok:
            return _BuildResult(False, f"npm run build failed:\n{build.log_tail()}")
        return _BuildResult(True, "")


async def code_node(state: AgentState) -> dict[str, Any]:
    """Generate the project files and verify the build in an E2B sandbox."""
    events.agent_start("code")
    retry = state.get("retry_count", 0)
    if retry:
        events.agent_progress("code", f"Regenerating after failure (attempt {retry + 1})")
    else:
        events.agent_progress("code", "Generating project files")

    model = models.get_chat_model("code")
    try:
        response = await model.ainvoke(_build_messages(state))
        file_tree = parse_file_tree(response.content)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Code agent produced invalid output: %s", exc)
        events.agent_error("code", "Could not parse generated files")
        return {"error": f"Code agent produced invalid output: {exc}", "build_success": False}
    except Exception as exc:  # noqa: BLE001 — surface provider/network errors to the pipeline
        logger.exception("Code agent model call failed")
        events.agent_error("code", str(exc))
        return {"error": f"Code agent failed: {exc}", "build_success": False}

    for path in file_tree:
        events.file_created(path)

    events.agent_progress("code", "Verifying build in sandbox")
    try:
        result = await _verify_build(file_tree)
    except Exception as exc:  # noqa: BLE001 — sandbox/network failure halts this run
        logger.exception("E2B sandbox failed")
        events.agent_error("code", f"Sandbox error: {exc}")
        return {"error": f"Sandbox error: {exc}", "file_tree": file_tree, "build_success": False}

    if result.ok:
        events.agent_complete("code")
        return {"file_tree": file_tree, "build_success": True, "build_error": None, "error": None}

    if retry < MAX_CODE_RETRIES:
        events.agent_progress("code", "Build failed — retrying with error context")
        return {
            "file_tree": file_tree,
            "build_success": False,
            "build_error": result.log,
            "retry_count": retry + 1,
        }

    events.agent_error("code", "Build failed after maximum retries")
    return {
        "file_tree": file_tree,
        "build_success": False,
        "build_error": result.log,
        "error": "Code agent could not produce a building project after retries",
    }

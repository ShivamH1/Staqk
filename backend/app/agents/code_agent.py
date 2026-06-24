from typing import Any

from app.agents import events
from app.agents.state import AgentState


async def code_node(state: AgentState) -> dict[str, Any]:
    """Generate all project files and verify the build in an E2B sandbox.

    Stub: returns an empty file tree and marks the build successful. Real Mistral
    Large generation + E2B verification lands in a later step.
    """
    events.agent_start("code")
    retry = state.get("retry_count", 0)
    if retry:
        events.agent_progress("code", f"Re-generating after failure (attempt {retry + 1})")
    else:
        events.agent_progress("code", "Generating project files")

    file_tree: dict[str, str] = {}

    events.agent_complete("code")
    return {"file_tree": file_tree, "build_success": True}

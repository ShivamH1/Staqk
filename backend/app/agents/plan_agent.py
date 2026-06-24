from typing import Any

from app.agents import events
from app.agents.state import AgentState


async def plan_node(state: AgentState) -> dict[str, Any]:
    """Convert the user's request into a structured architecture plan.

    Stub: returns an empty plan shell. Real Gemini Flash integration lands in a
    later step (see ai-pipeline.md → Plan Agent).
    """
    events.agent_start("plan")
    events.agent_progress("plan", "Analysing request and drafting architecture")

    plan: dict[str, Any] = {
        "components": [],
        "routes": [],
        "db_schema": [],
        "api_endpoints": [],
        "notes": "stub plan — model integration pending",
    }

    events.agent_complete("plan")
    return {"plan": plan}

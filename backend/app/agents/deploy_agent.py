from typing import Any

from app.agents import events
from app.agents.state import AgentState


async def deploy_node(state: AgentState) -> dict[str, Any]:
    """Deploy the final file tree to Vercel and return the live URL.

    No LLM — pure Vercel API. Stub: returns a placeholder URL. Real Vercel
    deployment lands in a later step.
    """
    events.agent_start("deploy")
    events.agent_progress("deploy", "Deploying to Vercel")

    deployment_url = "https://placeholder.staqk.app"

    events.agent_complete("deploy")
    return {"deployment_url": deployment_url}

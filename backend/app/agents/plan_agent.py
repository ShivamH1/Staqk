import json
import logging
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agents import events, models
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

PLAN_SYSTEM_PROMPT = """You are the Plan Agent for Staqk. Given a user request and \
tech stack, output a structured JSON plan.
Rules:
- Be specific about component names and file paths
- Keep the scope minimal — only what the user asked for
- Do not invent features not mentioned
- Output valid JSON only, no markdown

The JSON must have this shape:
{
  "components": ["ComponentName"],
  "routes": [{"path": "/", "component": "Home", "auth": false}],
  "db_schema": [{"model": "User", "fields": ["id", "email"]}],
  "api_endpoints": [{"method": "GET", "path": "/api/users"}],
  "notes": "string"
}"""


def _content_to_text(content: str | list[str | dict[str, Any]]) -> str:
    """Normalise a message content (str or content-block list) to plain text."""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and "text" in block:
            parts.append(str(block["text"]))
    return "".join(parts)


def parse_plan_json(content: str | list[str | dict[str, Any]]) -> dict[str, Any]:
    """Extract a JSON plan from an LLM response, tolerating ```json fences."""
    text = _content_to_text(content).strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    parsed: dict[str, Any] = json.loads(text)
    return parsed


def _build_user_prompt(state: AgentState) -> str:
    tech = state.get("tech_stack") or {}
    return (
        f"Tech stack: {json.dumps(tech)}\n\n"
        f"User request:\n{state.get('user_message', '')}"
    )


async def plan_node(state: AgentState) -> dict[str, Any]:
    """Convert the user's request into a structured architecture plan via the LLM."""
    events.agent_start("plan")
    events.agent_progress("plan", "Analysing request and drafting architecture")

    model = models.get_chat_model("plan")
    messages: list[BaseMessage] = [
        SystemMessage(content=PLAN_SYSTEM_PROMPT),
        HumanMessage(content=_build_user_prompt(state)),
    ]

    try:
        response = await model.ainvoke(messages)
        plan = parse_plan_json(response.content)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Plan agent could not parse model output: %s", exc)
        events.agent_error("plan", "Could not parse plan output")
        return {"error": f"Plan agent failed to produce valid JSON: {exc}"}
    except Exception as exc:  # noqa: BLE001 — surface provider/network errors to the pipeline
        logger.exception("Plan agent model call failed")
        events.agent_error("plan", str(exc))
        return {"error": f"Plan agent failed: {exc}"}

    events.agent_complete("plan")
    return {"plan": plan}

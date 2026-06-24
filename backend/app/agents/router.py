"""Model routing: maps each agent to its provider/model with an OpenRouter fallback.

Real model construction is wired up in a later step. This module centralises the
routing table so nodes call `get_model(agent)` rather than hard-coding providers.
"""

from dataclasses import dataclass

from app.agents.events import AgentName


@dataclass(frozen=True)
class ModelChoice:
    provider: str  # "gemini" | "mistral" | "groq" | "openrouter"
    model: str
    fallback_model: str  # OpenRouter slug used when the direct provider rate-limits


ROUTING: dict[AgentName, ModelChoice] = {
    "plan": ModelChoice("gemini", "gemini-1.5-flash", "google/gemini-flash-1.5"),
    "code": ModelChoice("mistral", "mistral-large-latest", "mistralai/mistral-large"),
    "test": ModelChoice("groq", "llama-3.1-70b-versatile", "meta-llama/llama-3.1-70b-instruct"),
    "security": ModelChoice("mistral", "mistral-small-latest", "mistralai/mistral-small"),
}


def get_model_choice(agent: AgentName) -> ModelChoice:
    if agent not in ROUTING:
        raise ValueError(f"No model routing configured for agent: {agent}")
    return ROUTING[agent]

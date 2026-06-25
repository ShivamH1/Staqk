"""Construct LangChain chat models per agent.

Routing table lives in `router.py`. This module turns a routing choice into a
live model: it prefers the direct provider when its API key is configured, and
otherwise falls back to OpenRouter (ADR-010).
"""

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from app.agents.events import AgentName
from app.agents.router import ModelChoice, get_model_choice
from app.config import settings

# Cap output tokens — controls cost and keeps requests within budget. Plans and
# per-file code chunks fit comfortably; raise per-agent later if needed.
MAX_OUTPUT_TOKENS = 4096


def _make_primary(choice: ModelChoice) -> BaseChatModel | None:
    """Build the direct-provider model if its API key is set, else None."""
    if choice.provider == "gemini" and settings.gemini_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=choice.model,
            google_api_key=SecretStr(settings.gemini_api_key),
            temperature=0,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
    if choice.provider == "mistral" and settings.mistral_api_key:
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(
            model_name=choice.model,
            api_key=SecretStr(settings.mistral_api_key),
            temperature=0,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
    if choice.provider == "groq" and settings.groq_api_key:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model_name=choice.model,
            api_key=SecretStr(settings.groq_api_key),
            temperature=0,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
    return None


def _make_openrouter(choice: ModelChoice) -> BaseChatModel | None:
    if not settings.openrouter_api_key:
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=choice.fallback_model,
        base_url="https://openrouter.ai/api/v1",
        api_key=SecretStr(settings.openrouter_api_key),
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
    )


def get_chat_model(agent: AgentName) -> BaseChatModel:
    """Return the chat model for an agent (direct provider, or OpenRouter)."""
    choice = get_model_choice(agent)
    model = _make_primary(choice) or _make_openrouter(choice)
    if model is None:
        raise RuntimeError(
            f"No model available for agent '{agent}': set its provider key or OPENROUTER_API_KEY"
        )
    return model

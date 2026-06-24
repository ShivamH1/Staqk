from datetime import UTC, datetime
from typing import Any, Literal

from langgraph.config import get_stream_writer

AgentName = Literal["plan", "code", "test", "security", "deploy"]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def emit(event: dict[str, Any]) -> None:
    """Write a custom event to the LangGraph stream.

    Consumed by the WebSocket handler via `graph.astream(..., stream_mode="custom")`.
    Safe to call inside a node; no-op if there is no active stream writer.
    """
    writer = get_stream_writer()
    if writer is not None:
        writer(event)


def agent_start(agent: AgentName) -> None:
    emit({"type": "agent_start", "agent": agent, "timestamp": _now()})


def agent_progress(agent: AgentName, message: str) -> None:
    emit({"type": "agent_progress", "agent": agent, "message": message, "timestamp": _now()})


def agent_complete(agent: AgentName) -> None:
    emit({"type": "agent_complete", "agent": agent, "timestamp": _now()})


def agent_error(agent: AgentName, error: str) -> None:
    emit({"type": "agent_error", "agent": agent, "error": error, "timestamp": _now()})


def file_created(path: str) -> None:
    emit({"type": "file_created", "path": path, "timestamp": _now()})


def test_result(file: str, passed: int, failed: int) -> None:
    emit({"type": "test_result", "file": file, "passed": passed, "failed": failed})


def security_finding(severity: str, rule: str, file: str) -> None:
    emit({"type": "security_finding", "severity": severity, "rule": rule, "file": file})


def pipeline_complete(deployment_url: str, credits_used: int) -> None:
    emit(
        {
            "type": "pipeline_complete",
            "deployment_url": deployment_url,
            "credits_used": credits_used,
        }
    )


def pipeline_error(error: str, credits_refunded: int) -> None:
    emit({"type": "pipeline_error", "error": error, "credits_refunded": credits_refunded})

import contextlib
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.agents.graph import pipeline
from app.agents.state import AgentState
from app.database import AsyncSessionLocal
from app.middleware.auth import verify_token_get_user
from app.services import credits as credit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


async def _refund_run(user_id: uuid.UUID, reason: str) -> None:
    """Refund a full pipeline run in its own session (best-effort)."""
    try:
        async with AsyncSessionLocal() as db:
            await credit_service.refund_credits(db, user_id, credit_service.PIPELINE_COST, reason)
    except Exception:  # noqa: BLE001 — a refund failure must not mask the original error
        logger.exception("Failed to refund credits for user %s", user_id)


@router.websocket("/stream/{project_id}")
async def stream_pipeline(websocket: WebSocket, project_id: str) -> None:
    """Run the agent pipeline and stream each event to the client.

    Auth: Clerk token as `?token=` query param (browsers can't set WS headers).
    Credits: `PIPELINE_COST` is deducted atomically *before* the pipeline starts
    (insufficient → error + close, nothing runs) and refunded if the run fails
    (agent error, disconnect, or crash).
    """
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    async with AsyncSessionLocal() as db:
        user = await verify_token_get_user(token, db)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    try:
        start_msg: dict[str, Any] = await websocket.receive_json()
    except WebSocketDisconnect:
        logger.info("Client disconnected before sending start message: %s", project_id)
        return

    # Pre-check + atomic deduction before any AI work runs.
    try:
        async with AsyncSessionLocal() as db:
            await credit_service.deduct_credits(
                db, user.id, credit_service.PIPELINE_COST, "Full pipeline run"
            )
    except credit_service.InsufficientCreditsError as exc:
        with contextlib.suppress(WebSocketDisconnect):
            await websocket.send_json(
                {"type": "pipeline_error", "error": str(exc), "credits_refunded": 0}
            )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient credits")
        return

    initial_state: AgentState = {
        "project_id": project_id,
        "user_message": start_msg.get("user_message", ""),
        "tech_stack": start_msg.get("tech_stack", {}),
        "existing_file_tree": start_msg.get("existing_file_tree", {}),
        "retry_count": 0,
    }

    try:
        deployment_url: str | None = None
        errored = False
        last_error = ""
        async for event in pipeline.astream(initial_state, stream_mode="custom"):
            await websocket.send_json(event)
            event_type = event.get("type")
            if event_type == "agent_error":
                errored = True
                last_error = event.get("error", "")
            elif event_type == "agent_complete" and event.get("agent") == "deploy":
                deployment_url = "pending"

        # An agent failure ends the stream without raising — refund and report.
        if errored:
            await _refund_run(user.id, f"Pipeline failed: {last_error}".strip())
            with contextlib.suppress(WebSocketDisconnect):
                await websocket.send_json(
                    {
                        "type": "pipeline_error",
                        "error": last_error or "Pipeline failed",
                        "credits_refunded": credit_service.PIPELINE_COST,
                    }
                )
        else:
            with contextlib.suppress(WebSocketDisconnect):
                await websocket.send_json(
                    {
                        "type": "pipeline_complete",
                        "deployment_url": deployment_url or "",
                        "credits_used": credit_service.PIPELINE_COST,
                    }
                )
    except WebSocketDisconnect:
        logger.info("Client disconnected during pipeline stream: %s", project_id)
        await _refund_run(user.id, "Client disconnected before completion")
    except Exception as exc:  # noqa: BLE001 — surface any pipeline failure to the client
        logger.exception("Pipeline error for project %s", project_id)
        await _refund_run(user.id, f"Pipeline error: {exc}")
        with contextlib.suppress(WebSocketDisconnect):
            await websocket.send_json(
                {
                    "type": "pipeline_error",
                    "error": str(exc),
                    "credits_refunded": credit_service.PIPELINE_COST,
                }
            )

import contextlib
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.agents.graph import pipeline
from app.agents.state import AgentState
from app.database import AsyncSessionLocal
from app.middleware.auth import verify_token_get_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


@router.websocket("/stream/{project_id}")
async def stream_pipeline(websocket: WebSocket, project_id: str) -> None:
    """Run the agent pipeline and stream each event to the client.

    Auth: Clerk token passed as `?token=` query param (browsers cannot set
    WebSocket headers). Credit checks/deduction are wired in a later step.
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
        initial_state: AgentState = {
            "project_id": project_id,
            "user_message": start_msg.get("user_message", ""),
            "tech_stack": start_msg.get("tech_stack", {}),
            "existing_file_tree": start_msg.get("existing_file_tree", {}),
            "retry_count": 0,
        }

        deployment_url: str | None = None
        async for event in pipeline.astream(initial_state, stream_mode="custom"):
            await websocket.send_json(event)
            if event.get("type") == "agent_complete" and event.get("agent") == "deploy":
                deployment_url = "pending"

        # TODO(step-5): deduct credits atomically and persist the run.
        await websocket.send_json(
            {
                "type": "pipeline_complete",
                "deployment_url": deployment_url or "",
                "credits_used": 5,
            }
        )
    except WebSocketDisconnect:
        logger.info("Client disconnected from pipeline stream: %s", project_id)
    except Exception as exc:  # noqa: BLE001 — surface any pipeline failure to the client
        logger.exception("Pipeline error for project %s", project_id)
        with contextlib.suppress(WebSocketDisconnect):
            await websocket.send_json(
                {"type": "pipeline_error", "error": str(exc), "credits_refunded": 5}
            )

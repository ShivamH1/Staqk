import contextlib
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.agents.graph import pipeline
from app.agents.state import AgentState
from app.database import AsyncSessionLocal
from app.middleware.auth import verify_token_get_user
from app.models.project import ProjectStatus, WebsiteProject
from app.models.user import User
from app.services import credits as credit_service
from app.services import projects as project_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


async def _refund(user_id: uuid.UUID, amount: int, reason: str) -> None:
    """Refund a run in its own session (best-effort)."""
    try:
        async with AsyncSessionLocal() as db:
            await credit_service.refund_credits(db, user_id, amount, reason)
    except Exception:  # noqa: BLE001 — a refund failure must not mask the original error
        logger.exception("Failed to refund credits for user %s", user_id)


async def _set_status(project_id: uuid.UUID, project_status: ProjectStatus) -> None:
    try:
        async with AsyncSessionLocal() as db:
            await project_service.set_status(db, project_id, project_status)
    except Exception:  # noqa: BLE001 — status persistence is non-fatal to the stream
        logger.exception("Failed to set status for project %s", project_id)


async def _resolve_project(
    websocket: WebSocket, user: User, project_id: str
) -> WebsiteProject | None:
    """Load the connecting user's project, or close the socket and return None."""
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid project id")
        return None
    async with AsyncSessionLocal() as db:
        project = await project_service.get_project(db, user.id, pid)
    if project is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Project not found")
    return project


async def _authenticate(websocket: WebSocket) -> User | None:
    """Accept, validate the `?token=` query param, return the user or close."""
    await websocket.accept()
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return None
    async with AsyncSessionLocal() as db:
        user = await verify_token_get_user(token, db)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
    return user


async def _run_pipeline(
    websocket: WebSocket,
    user: User,
    project: WebsiteProject,
    *,
    cost: int,
    initial_state: AgentState,
) -> None:
    """Deduct, run the pipeline, stream events, then persist + settle credits.

    Credits are deducted before any AI work (insufficient → close, nothing runs)
    and refunded if the run fails. The project's `file_tree`/`status` are persisted
    so a run survives the socket closing.
    """
    try:
        async with AsyncSessionLocal() as db:
            await credit_service.deduct_credits(db, user.id, cost, "Pipeline run")
    except credit_service.InsufficientCreditsError as exc:
        with contextlib.suppress(WebSocketDisconnect):
            await websocket.send_json(
                {"type": "pipeline_error", "error": str(exc), "credits_refunded": 0}
            )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient credits")
        return

    await _set_status(project.id, ProjectStatus.building)

    try:
        # "custom" carries the agent events we stream; "values" carries the final
        # AgentState we persist (file_tree, error, deployment_url). `astream` with a
        # mode list yields loosely-typed (mode, chunk) tuples.
        final_state: Any = {}
        async for mode, chunk in pipeline.astream(initial_state, stream_mode=["custom", "values"]):
            if mode == "custom":
                await websocket.send_json(chunk)
            else:
                final_state = chunk

        error = final_state.get("error")
        if error:
            await _refund(user.id, cost, f"Pipeline failed: {error}")
            await _set_status(project.id, ProjectStatus.error)
            with contextlib.suppress(WebSocketDisconnect):
                await websocket.send_json(
                    {"type": "pipeline_error", "error": error, "credits_refunded": cost}
                )
            return

        file_tree: dict[str, str] = final_state.get("file_tree", {})
        deployment_url = final_state.get("deployment_url")
        final_status = ProjectStatus.deployed if deployment_url else ProjectStatus.ready
        try:
            async with AsyncSessionLocal() as db:
                await project_service.save_run_result(db, project.id, file_tree, final_status)
        except Exception:  # noqa: BLE001 — persistence failure shouldn't drop the result event
            logger.exception("Failed to persist run result for project %s", project.id)

        with contextlib.suppress(WebSocketDisconnect):
            await websocket.send_json(
                {
                    "type": "pipeline_complete",
                    "deployment_url": deployment_url or "",
                    "credits_used": cost,
                }
            )
    except WebSocketDisconnect:
        logger.info("Client disconnected during pipeline stream: %s", project.id)
        await _refund(user.id, cost, "Client disconnected before completion")
        await _set_status(project.id, ProjectStatus.error)
    except Exception as exc:  # noqa: BLE001 — surface any pipeline failure to the client
        logger.exception("Pipeline error for project %s", project.id)
        await _refund(user.id, cost, f"Pipeline error: {exc}")
        await _set_status(project.id, ProjectStatus.error)
        with contextlib.suppress(WebSocketDisconnect):
            await websocket.send_json(
                {"type": "pipeline_error", "error": str(exc), "credits_refunded": cost}
            )


@router.websocket("/stream/{project_id}")
async def stream_pipeline(websocket: WebSocket, project_id: str) -> None:
    """Run the full agent pipeline for a project and stream each event.

    Auth: Clerk token as `?token=` query param (browsers can't set WS headers).
    """
    user = await _authenticate(websocket)
    if user is None:
        return
    project = await _resolve_project(websocket, user, project_id)
    if project is None:
        return

    try:
        start_msg: dict[str, Any] = await websocket.receive_json()
    except WebSocketDisconnect:
        logger.info("Client disconnected before start message: %s", project_id)
        return

    initial_state: AgentState = {
        "project_id": project_id,
        "user_message": start_msg.get("user_message", ""),
        "tech_stack": start_msg.get("tech_stack") or project.tech_stack,
        "existing_file_tree": start_msg.get("existing_file_tree", {}),
        "retry_count": 0,
    }
    await _run_pipeline(
        websocket, user, project, cost=credit_service.PIPELINE_COST, initial_state=initial_state
    )


@router.websocket("/iterate/{project_id}")
async def iterate_pipeline(websocket: WebSocket, project_id: str) -> None:
    """Chat iteration: re-run the pipeline over the project's existing file tree.

    Cheaper than a full run (`CHAT_ITERATION_COST`); seeds `existing_file_tree`
    from the saved project so agents revise rather than regenerate.
    """
    user = await _authenticate(websocket)
    if user is None:
        return
    project = await _resolve_project(websocket, user, project_id)
    if project is None:
        return

    try:
        start_msg: dict[str, Any] = await websocket.receive_json()
    except WebSocketDisconnect:
        logger.info("Client disconnected before iterate message: %s", project_id)
        return

    initial_state: AgentState = {
        "project_id": project_id,
        "user_message": start_msg.get("user_message", ""),
        "tech_stack": project.tech_stack,
        "existing_file_tree": project.file_tree,
        "retry_count": 0,
    }
    await _run_pipeline(
        websocket,
        user,
        project,
        cost=credit_service.CHAT_ITERATION_COST,
        initial_state=initial_state,
    )

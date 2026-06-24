import hashlib
import hmac
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.services import users as user_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_clerk_webhook(payload: bytes, svix_id: str, svix_ts: str, svix_signature: str) -> None:
    """Verify Clerk webhook signature using svix."""
    # Replay attack protection — reject if timestamp is > 5 minutes old
    try:
        ts = int(svix_ts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid timestamp") from exc
    if abs(time.time() - ts) > 300:
        raise HTTPException(status_code=400, detail="Timestamp out of range")

    signed_content = f"{svix_id}.{svix_ts}.{payload.decode()}".encode()
    secret_bytes = settings.clerk_webhook_secret.replace("whsec_", "")
    import base64
    secret = base64.b64decode(secret_bytes)
    expected = hmac.new(secret, signed_content, hashlib.sha256).digest()
    expected_b64 = base64.b64encode(expected).decode()

    signatures = svix_signature.split(" ")
    if not any(sig.split(",", 1)[-1] == expected_b64 for sig in signatures):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/webhook", status_code=200)
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    svix_id: str = Header(..., alias="svix-id"),
    svix_timestamp: str = Header(..., alias="svix-timestamp"),
    svix_signature: str = Header(..., alias="svix-signature"),
) -> dict[str, str]:
    body = await request.body()
    _verify_clerk_webhook(body, svix_id, svix_timestamp, svix_signature)

    event: dict[str, Any] = await request.json()
    event_type: str = event.get("type", "")

    if event_type == "user.created":
        data = event.get("data", {})
        clerk_id: str = data.get("id", "")
        email_addresses: list[dict[str, Any]] = data.get("email_addresses", [])
        primary_id = data.get("primary_email_address_id")
        email = next(
            (e["email_address"] for e in email_addresses if e.get("id") == primary_id),
            email_addresses[0]["email_address"] if email_addresses else "",
        )
        if clerk_id and email:
            async with db.begin():
                existing = await user_service.get_by_clerk_id(clerk_id, db)
                if existing is None:
                    await user_service.create_user(clerk_id, email, db)
                    logger.info("Synced new user from Clerk: %s", clerk_id)

    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

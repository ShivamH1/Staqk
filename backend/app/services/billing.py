"""Razorpay payments for credit purchases.

India-first: Stripe India is invite-only and tangled in RBI e-mandate rules, so
credits are bought through Razorpay (ADR-013). This module only *creates* orders;
the ledger is credited later by the webhook (verified server-side) so a forged
client callback can never grant credits.

The Razorpay SDK is synchronous (requests-based), so every call is wrapped in
`run_in_threadpool` to honour the no-sync-IO-in-async-handlers rule.
"""

import hashlib
import hmac
import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services import credits as credit_service

if TYPE_CHECKING:
    import razorpay

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreditPack:
    id: str
    credits: int
    amount: int  # smallest currency unit — paise for INR (₹1 = 100 paise)
    currency: str = "INR"


# Credit packs are product pricing (like PIPELINE_COST) — fixed, not configurable.
CREDIT_PACKS: dict[str, CreditPack] = {
    "credits_100": CreditPack("credits_100", 100, 79900),  # ₹799
    "credits_500": CreditPack("credits_500", 500, 349900),  # ₹3,499
    "credits_2000": CreditPack("credits_2000", 2000, 1199900),  # ₹11,999
}


class PaymentError(Exception):
    """Razorpay is unavailable or misconfigured. Maps to HTTP 503."""


class UnknownPackError(Exception):
    """Requested credit pack id doesn't exist. Maps to HTTP 404."""


_client: "razorpay.Client | None" = None


def get_client() -> "razorpay.Client":
    """Return a cached Razorpay client, or raise `PaymentError` if unconfigured."""
    global _client
    if _client is None:
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise PaymentError("Razorpay is not configured")
        import razorpay  # lazy: keep the SDK off the import path until first use

        _client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    return _client


async def create_order(user_id: uuid.UUID, pack_id: str) -> dict[str, Any]:
    """Create a Razorpay order for a credit pack.

    The buyer and the pack's credits are stamped into the order `notes`; the
    webhook reads them back to credit the right ledger after Razorpay confirms
    payment — no pending-order row required.
    """
    pack = CREDIT_PACKS.get(pack_id)
    if pack is None:
        raise UnknownPackError(pack_id)

    client = get_client()
    data = {
        "amount": pack.amount,
        "currency": pack.currency,
        "receipt": f"rcpt_{uuid.uuid4().hex[:24]}",
        "notes": {
            "user_id": str(user_id),
            "pack_id": pack.id,
            "credits": str(pack.credits),
        },
    }
    try:
        order: dict[str, Any] = await run_in_threadpool(client.order.create, data=data)
    except Exception as exc:  # noqa: BLE001 — surface any SDK/network failure as PaymentError
        logger.exception("Razorpay order creation failed for user %s", user_id)
        raise PaymentError("Failed to create payment order") from exc

    logger.info("Created Razorpay order %s for user %s (%s)", order.get("id"), user_id, pack.id)
    return order


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify a Razorpay webhook's HMAC-SHA256 signature against the raw body.

    Returns False (rejecting the delivery) if no webhook secret is configured —
    we never trust an unverifiable payload.
    """
    secret = settings.razorpay_webhook_secret
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def handle_webhook_event(db: AsyncSession, payload: dict[str, Any]) -> None:
    """Credit a user after Razorpay confirms an order is paid.

    Listens for `order.paid` (the order entity carries the `notes` we stamped at
    creation; the payment entity gives a stable id for idempotency). Credits and
    buyer are read from the trusted server-set notes — never from the client.
    """
    if payload.get("event") != "order.paid":
        return

    entities = payload.get("payload", {})
    order = entities.get("order", {}).get("entity", {})
    payment = entities.get("payment", {}).get("entity", {})
    notes = order.get("notes") or {}
    reference = payment.get("id") or order.get("id")

    user_id_raw = notes.get("user_id")
    credits_raw = notes.get("credits")
    if not (user_id_raw and credits_raw and reference):
        logger.warning("order.paid webhook missing user_id/credits/reference; ignoring")
        return

    try:
        user_id = uuid.UUID(str(user_id_raw))
        credit_amount = int(credits_raw)
    except (ValueError, TypeError):
        logger.warning("order.paid webhook has malformed notes; ignoring")
        return

    await credit_service.credit_purchase(
        db,
        user_id,
        credit_amount,
        reference=str(reference),
        description=f"Purchased {credit_amount} credits",
    )

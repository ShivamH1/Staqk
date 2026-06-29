import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.billing import (
    CreateOrderRequest,
    CreateOrderResponse,
    CreditPackInfo,
    TransactionResponse,
)
from app.services import billing as billing_service
from app.services import credits as credit_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/packs", response_model=list[CreditPackInfo])
async def list_packs() -> list[CreditPackInfo]:
    """The purchasable credit packs (single source of truth for prices)."""
    return [
        CreditPackInfo(id=pack.id, credits=pack.credits, amount=pack.amount, currency=pack.currency)
        for pack in billing_service.CREDIT_PACKS.values()
    ]


@router.post("/order", response_model=CreateOrderResponse)
async def create_order(
    body: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
) -> CreateOrderResponse:
    """Create a Razorpay order the browser can pay via Checkout.

    Credits are *not* granted here — only after the webhook confirms payment.
    """
    try:
        order = await billing_service.create_order(current_user.id, body.pack_id)
    except billing_service.UnknownPackError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown credit pack"
        ) from exc
    except billing_service.PaymentError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    pack = billing_service.CREDIT_PACKS[body.pack_id]
    return CreateOrderResponse(
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        key_id=settings.razorpay_key_id,
        credits=pack.credits,
        pack_id=pack.id,
    )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    signature: str = Header("", alias="X-Razorpay-Signature"),
) -> dict[str, str]:
    """Receive Razorpay events. Verifies the signature against the raw body, then
    credits the buyer on `order.paid`. Credits are granted *only* here — never
    from a client callback — and idempotently, so replays are safe."""
    body = await request.body()
    if not billing_service.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload: dict[str, Any] = json.loads(body)
    await billing_service.handle_webhook_event(db, payload)
    return {"status": "ok"}


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Row[Any]]:
    """The signed-in user's credit ledger, newest first."""
    return await credit_service.list_transactions(db, current_user.id)

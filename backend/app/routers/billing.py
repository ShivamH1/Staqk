from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.billing import CreateOrderRequest, CreateOrderResponse, CreditPackInfo
from app.services import billing as billing_service

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

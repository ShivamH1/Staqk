import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.transaction import TransactionType


class CreditPackInfo(BaseModel):
    """A purchasable credit pack. `amount` is in the smallest currency unit
    (paise for INR), matching what the order endpoint charges."""

    id: str
    credits: int
    amount: int
    currency: str


class CreateOrderRequest(BaseModel):
    pack_id: str


class CreateOrderResponse(BaseModel):
    """Everything the frontend needs to open Razorpay Checkout."""

    order_id: str
    amount: int
    currency: str
    key_id: str  # public Razorpay key id — safe to expose to the browser
    credits: int
    pack_id: str


class TransactionResponse(BaseModel):
    """A ledger entry for the billing history. `amount` is signed credits
    (positive for purchase/refund, negative for spend)."""

    id: uuid.UUID
    amount: int
    type: TransactionType
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}

from pydantic import BaseModel


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

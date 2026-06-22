from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    address_id: int


class CreatePaymentRequest(BaseModel):
    address_id: int


class CreatePaymentResponse(BaseModel):
    razorpay_order_id: str
    amount: float
    currency: str = "INR"
    razorpay_key_id: str


class VerifyPaymentResponse(BaseModel):
    order_id: int
    razorpay_order_id: str
    razorpay_payment_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    subtotal: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: OrderStatus
    shipping_name: str
    shipping_phone: str
    shipping_address_line_1: str
    shipping_address_line_2: Optional[str] = None
    shipping_city: str
    shipping_state: str
    shipping_country: str
    shipping_pincode: str
    subtotal: float
    total: float
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    payment_status: Optional[str] = None
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

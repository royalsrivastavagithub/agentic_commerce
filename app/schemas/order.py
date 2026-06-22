from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    address_id: int


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
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

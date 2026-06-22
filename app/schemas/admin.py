from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.order import OrderStatus


class AdminUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    is_verified: bool
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    order_count: int = 0
    total_spent: float = 0.0


class DashboardSummary(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: float
    avg_order_value: float
    orders_by_status: dict[str, int]
    low_stock_count: int


class RevenuePoint(BaseModel):
    date: str
    revenue: float


class TopProduct(BaseModel):
    id: int
    title: str
    total_quantity: int
    total_revenue: float


class RecentOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_email: str
    status: OrderStatus
    total: float
    created_at: datetime


class RecentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class OrderStatus(str, enum.Enum):
    PAID = "PAID"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PAID, nullable=False)
    shipping_name = Column(String, nullable=False)
    shipping_phone = Column(String, nullable=False)
    shipping_address_line_1 = Column(String, nullable=False)
    shipping_address_line_2 = Column(String, nullable=True)
    shipping_city = Column(String, nullable=False)
    shipping_state = Column(String, nullable=False)
    shipping_country = Column(String, nullable=False)
    shipping_pincode = Column(String, nullable=False)
    subtotal = Column(Float, nullable=False)
    total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Payment fields
    razorpay_order_id = Column(String, nullable=True, index=True)
    razorpay_payment_id = Column(String, nullable=True)
    payment_status = Column(String, nullable=True, default=None)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)
    thumbnail = Column(String, nullable=True)

    order = relationship("Order", back_populates="items")

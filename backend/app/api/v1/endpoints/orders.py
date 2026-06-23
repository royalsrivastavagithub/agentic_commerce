from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    OrderResponse,
    VerifyPaymentRequest,
)
from app.api.deps import get_current_user
from app.models.user import User
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/create-payment",
    response_model=CreatePaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate payment: validate cart, create Razorpay order (no Order created yet)",
)
def create_payment(
    req: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.create_razorpay_payment(db, current_user.id, req.address_id)


@router.post(
    "/verify-payment",
    summary="Verify Razorpay payment signature, create Order, deduct stock, clear cart",
)
def verify_payment(
    req: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.verify_and_create_order(db, current_user, req)


@router.get("", response_model=list[OrderResponse], summary="List current user orders")
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.get_user_orders(db, current_user.id)


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order by ID")
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.get_user_order(db, current_user.id, order_id)

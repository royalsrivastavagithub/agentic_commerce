from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.address import Address
from app.models.cart import Cart
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.pending_payment import PendingPayment
from app.schemas.order import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    OrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.api.deps import get_current_user
from app.models.user import User
from app.services.razorpay import (
    create_razorpay_order,
    verify_payment_signature,
)
from app.core.config import settings

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
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    address = (
        db.query(Address)
        .filter(Address.id == req.address_id, Address.user_id == current_user.id)
        .first()
    )
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product (id={cart_item.product_id}) no longer exists",
            )
        if cart_item.quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.title}': {product.stock} available, {cart_item.quantity} requested",
            )

    total = sum(
        round(cart_item.quantity * (db.query(Product).filter(Product.id == cart_item.product_id).first().price), 2)
        for cart_item in cart.items
    )

    try:
        razorpay_order = create_razorpay_order(
            amount=total,
            currency="INR",
            receipt=f"pay_{current_user.id}_{datetime.utcnow().timestamp()}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create Razorpay order: {str(e)}",
        )

    pending = PendingPayment(
        user_id=current_user.id,
        address_id=req.address_id,
        razorpay_order_id=razorpay_order["id"],
        amount=total,
    )
    db.add(pending)
    db.commit()

    return CreatePaymentResponse(
        razorpay_order_id=razorpay_order["id"],
        amount=total,
        currency="INR",
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post(
    "/verify-payment",
    summary="Verify Razorpay payment signature, create Order, deduct stock, clear cart",
)
def verify_payment(
    req: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pending = (
        db.query(PendingPayment)
        .filter(
            PendingPayment.razorpay_order_id == req.razorpay_order_id,
            PendingPayment.user_id == current_user.id,
        )
        .first()
    )
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment session not found",
        )

    if not verify_payment_signature(
        req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed",
        )

    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    address = db.query(Address).filter(Address.id == pending.address_id).first()

    shipping_name = (
        f"{current_user.first_name or ''} {current_user.last_name or ''}".strip()
        or current_user.email
    )

    order = Order(
        user_id=current_user.id,
        status=OrderStatus.PAID,
        shipping_name=shipping_name,
        shipping_phone=current_user.phone or "",
        shipping_address_line_1=address.street if address else "",
        shipping_address_line_2=None,
        shipping_city=address.city if address else "",
        shipping_state=address.state if address else "",
        shipping_country=address.country if address else "",
        shipping_pincode=address.pincode if address else "",
        subtotal=0.0,
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        payment_status="paid",
    )
    db.add(order)
    db.flush()

    subtotal = 0.0
    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product (id={cart_item.product_id}) no longer exists",
            )
        if cart_item.quantity > product.stock:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.title}'",
            )
        item_subtotal = round(cart_item.quantity * product.price, 2)
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.title,
            product_price=product.price,
            quantity=cart_item.quantity,
            subtotal=item_subtotal,
        )
        db.add(order_item)
        product.stock -= cart_item.quantity
        subtotal += item_subtotal

    order.subtotal = round(subtotal, 2)
    order.total = order.subtotal

    cart.items = []
    db.delete(pending)
    db.commit()
    db.refresh(order)

    return order


@router.get("", response_model=list[OrderResponse], summary="List current user orders")
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order by ID")
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order

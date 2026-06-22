from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    order_in: OrderCreate,
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
        .filter(Address.id == order_in.address_id, Address.user_id == current_user.id)
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

    shipping_name = (
        f"{current_user.first_name or ''} {current_user.last_name or ''}".strip()
        or current_user.email
    )

    order = Order(
        user_id=current_user.id,
        status=OrderStatus.PENDING,
        shipping_name=shipping_name,
        shipping_phone=current_user.phone or "",
        shipping_address_line_1=address.street,
        shipping_address_line_2=None,
        shipping_city=address.city,
        shipping_state=address.state,
        shipping_country=address.country,
        shipping_pincode=address.pincode,
        subtotal=0.0,
    )
    db.add(order)
    db.flush()

    subtotal = 0.0
    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
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
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderResponse])
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


@router.get("/{order_id}", response_model=OrderResponse)
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


@router.put("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
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
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{order.status.value}' status",
        )
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, BadRequestError, BadGatewayError
from app.models.address import Address
from app.models.cart import Cart
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.pending_payment import PendingPayment
from app.models.user import User
from app.schemas.order import CreatePaymentResponse
from app.services.razorpay import create_razorpay_order, verify_payment_signature
from app.core.config import settings


def find_pending(db: Session, razorpay_order_id: str, user_id: int | None = None) -> PendingPayment:
    query = db.query(PendingPayment).filter(PendingPayment.razorpay_order_id == razorpay_order_id)
    if user_id is not None:
        query = query.filter(PendingPayment.user_id == user_id)
    pending = query.first()
    if not pending:
        raise NotFoundError("Payment session not found")
    return pending


def validate_cart_for_checkout(db: Session, user_id: int, address_id: int) -> tuple[Cart, Address, float]:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        raise BadRequestError("Cart is empty")

    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user_id)
        .first()
    )
    if not address:
        raise NotFoundError("Address not found")

    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            raise BadRequestError(f"Product (id={cart_item.product_id}) no longer exists")
        if cart_item.quantity > product.stock:
            raise BadRequestError(
                f"Insufficient stock for '{product.title}': {product.stock} available, {cart_item.quantity} requested"
            )

    total = sum(
        round(cart_item.quantity * cart_item.product_price, 2)
        for cart_item in cart.items
    )
    return cart, address, total


def create_razorpay_payment(db: Session, user_id: int, address_id: int) -> CreatePaymentResponse:
    _, _, total = validate_cart_for_checkout(db, user_id, address_id)

    try:
        razorpay_order = create_razorpay_order(
            amount=total,
            currency="INR",
            receipt=f"pay_{user_id}_{datetime.now(timezone.utc).timestamp()}",
        )
    except Exception as e:
        raise BadGatewayError(f"Failed to create Razorpay order: {str(e)}")

    pending = PendingPayment(
        user_id=user_id,
        address_id=address_id,
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


def build_order_and_items(
    db: Session,
    user: User,
    cart: Cart,
    address: Address | None,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    *,
    price_attr: str = "product_price",
    strict_stock: bool = True,
) -> tuple[Order, float]:
    shipping_name = (
        f"{user.first_name or ''} {user.last_name or ''}".strip()
        or user.email
    )

    order = Order(
        user_id=user.id,
        status=OrderStatus.PAID,
        shipping_name=shipping_name,
        shipping_phone=user.phone or "",
        shipping_address_line_1=address.street if address else "",
        shipping_address_line_2=None,
        shipping_city=address.city if address else "",
        shipping_state=address.state if address else "",
        shipping_country=address.country if address else "",
        shipping_pincode=address.pincode if address else "",
        subtotal=0.0,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        payment_status="paid",
    )
    db.add(order)
    db.flush()

    subtotal = 0.0
    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            if strict_stock:
                db.rollback()
                raise BadRequestError(f"Product (id={cart_item.product_id}) no longer exists")
            continue
        if cart_item.quantity > product.stock:
            if strict_stock:
                db.rollback()
                raise BadRequestError(f"Insufficient stock for '{product.title}'")
            continue

        unit_price = getattr(cart_item, price_attr, product.price)
        item_subtotal = round(cart_item.quantity * unit_price, 2)
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.title,
            product_price=unit_price,
            quantity=cart_item.quantity,
            subtotal=item_subtotal,
            thumbnail=product.thumbnail,
        )
        db.add(order_item)
        product.stock -= cart_item.quantity
        subtotal += item_subtotal

    order.subtotal = round(subtotal, 2)
    order.total = order.subtotal
    return order, subtotal


def finalize_order(db: Session, order: Order, cart: Cart, pending: PendingPayment) -> Order:
    cart.items = []
    db.delete(pending)
    db.commit()
    db.refresh(order)
    return order


def verify_and_create_order(
    db: Session, user: User, req,
) -> Order:
    pending = find_pending(db, req.razorpay_order_id, user_id=user.id)

    if not verify_payment_signature(
        req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature
    ):
        raise BadRequestError("Payment signature verification failed")

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise BadRequestError("Cart is empty")

    address = db.query(Address).filter(Address.id == pending.address_id).first()

    order, _ = build_order_and_items(
        db, user, cart, address,
        req.razorpay_order_id, req.razorpay_payment_id,
        price_attr="product_price", strict_stock=True,
    )

    return finalize_order(db, order, cart, pending)


def get_user_orders(db: Session, user_id: int) -> list[Order]:
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_user_order(db: Session, user_id: int, order_id: int) -> Order:
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )
    if not order:
        raise NotFoundError("Order not found")
    return order

import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.cart import Cart
from app.models.pending_payment import PendingPayment
from app.models.address import Address
from app.models.user import User
from app.services.razorpay import verify_webhook_signature
from app.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"], include_in_schema=False)


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    payload = json.loads(body)
    event = payload.get("event", "")

    if event == "payment.captured":
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payment.get("order_id", "")
        razorpay_payment_id = payment.get("id", "")

        db = SessionLocal()
        try:
            order = (
                db.query(Order)
                .filter(Order.razorpay_order_id == razorpay_order_id)
                .first()
            )
            if order:
                if order.status == OrderStatus.PAID:
                    return {"status": "ignored", "reason": "order_already_paid"}
                return {"status": "ignored", "reason": f"order_status_{order.status.value}"}

            pending = (
                db.query(PendingPayment)
                .filter(PendingPayment.razorpay_order_id == razorpay_order_id)
                .first()
            )
            if not pending:
                return {"status": "ignored", "reason": "order_not_found"}

            user = db.query(User).filter(User.id == pending.user_id).first()
            address = db.query(Address).filter(Address.id == pending.address_id).first()
            cart = db.query(Cart).filter(Cart.user_id == pending.user_id).first()

            if not cart or not cart.items:
                return {"status": "ignored", "reason": "cart_empty"}

            shipping_name = (
                f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
            )

            order = Order(
                user_id=pending.user_id,
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
                if product and cart_item.quantity <= product.stock:
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
        except Exception:
            db.rollback()
        finally:
            db.close()

    return {"status": "ok"}

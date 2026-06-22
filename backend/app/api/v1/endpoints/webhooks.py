import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.cart import Cart
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
            if not order:
                return {"status": "ignored", "reason": "order_not_found"}

            if order.status != OrderStatus.PENDING_PAYMENT:
                return {"status": "ignored", "reason": f"order_status_{order.status.value}"}

            for order_item in order.items:
                product = db.query(Product).filter(Product.id == order_item.product_id).first()
                if product and order_item.quantity <= product.stock:
                    product.stock -= order_item.quantity

            cart = db.query(Cart).filter(Cart.user_id == order.user_id).first()
            if cart:
                cart.items = []

            order.status = OrderStatus.PAID
            order.razorpay_payment_id = razorpay_payment_id
            order.payment_status = "paid"
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    return {"status": "ok"}

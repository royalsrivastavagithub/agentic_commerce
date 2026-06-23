import json

from fastapi import APIRouter, HTTPException, Request, status

from app.db.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.cart import Cart
from app.models.pending_payment import PendingPayment
from app.models.address import Address
from app.models.user import User
from app.services.razorpay import verify_webhook_signature
from app.services import order_service

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

            order, _ = order_service.build_order_and_items(
                db, user, cart, address,
                razorpay_order_id, razorpay_payment_id,
                price_attr="price", strict_stock=False,
            )

            cart.items = []
            db.delete(pending)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    return {"status": "ok"}

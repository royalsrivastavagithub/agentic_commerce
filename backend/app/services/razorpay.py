import hashlib
import hmac
import json

import razorpay

from app.core.config import settings


def get_razorpay_client() -> razorpay.Client:
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount: float, currency: str = "INR", receipt: str | None = None) -> dict:
    client = get_razorpay_client()
    amount_paise = int(round(amount * 100))
    data = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt or "",
    }
    return client.order.create(data)


def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, razorpay_signature)


def verify_webhook_signature(body: bytes, signature_header: str) -> bool:
    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

import hashlib
import hmac
import json

import pytest

from app.core.config import settings
from app.services.razorpay import verify_payment_signature, verify_webhook_signature


skip_no_key = pytest.mark.skipif(
    not settings.RAZORPAY_KEY_SECRET or not settings.RAZORPAY_WEBHOOK_SECRET,
    reason="RAZORPAY_KEY_SECRET or RAZORPAY_WEBHOOK_SECRET not set",
)


class TestVerifyPaymentSignature:
    @skip_no_key
    def test_valid_signature_returns_true(self):
        order_id = "order_abc123"
        payment_id = "pay_def456"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert verify_payment_signature(order_id, payment_id, expected) is True

    @skip_no_key
    def test_invalid_signature_returns_false(self):
        assert verify_payment_signature("o1", "p1", "totally_wrong_sig") is False

    @skip_no_key
    def test_empty_signature_returns_false(self):
        assert verify_payment_signature("o1", "p1", "") is False

    @skip_no_key
    def test_wrong_order_id_returns_false(self):
        sig = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            b"real_order|real_pay",
            hashlib.sha256,
        ).hexdigest()
        assert verify_payment_signature("wrong_order", "real_pay", sig) is False


class TestVerifyWebhookSignature:
    @skip_no_key
    def test_valid_webhook_signature_returns_true(self):
        body = json.dumps({"event": "payment.captured", "payload": {}}).encode("utf-8")
        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        assert verify_webhook_signature(body, expected) is True

    @skip_no_key
    def test_invalid_webhook_signature_returns_false(self):
        body = json.dumps({"event": "payment.captured"}).encode("utf-8")
        assert verify_webhook_signature(body, "bad_signature") is False

    @skip_no_key
    def test_empty_signature_header_returns_false(self):
        body = json.dumps({"event": "payment.captured"}).encode("utf-8")
        assert verify_webhook_signature(body, "") is False

    @skip_no_key
    def test_tampered_body_returns_false(self):
        body = json.dumps({"event": "payment.captured", "amount": 100}).encode("utf-8")
        sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        tampered = json.dumps({"event": "payment.captured", "amount": 999}).encode("utf-8")
        assert verify_webhook_signature(tampered, sig) is False

    @skip_no_key
    def test_empty_body_returns_false(self):
        sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            b"",
            hashlib.sha256,
        ).hexdigest()
        assert verify_webhook_signature(b"non_empty", sig) is False

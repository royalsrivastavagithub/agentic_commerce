import pytest

from app.core.config import settings
from app.services.razorpay import create_razorpay_order, get_razorpay_client


skip_no_key = pytest.mark.skipif(
    not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET,
    reason="RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set",
)


class TestRazorpayIntegration:
    @skip_no_key
    def test_create_order_success(self):
        order = create_razorpay_order(amount=1.0, currency="INR", receipt="test_int_001")
        assert "id" in order
        assert order["id"].startswith("order_")
        assert order["amount"] == 100
        assert order["currency"] == "INR"
        assert order["status"] == "created"

    @skip_no_key
    def test_create_order_with_custom_receipt(self):
        receipt = f"test_receipt_unique"
        order = create_razorpay_order(amount=5.50, currency="INR", receipt=receipt)
        assert order["receipt"] == receipt
        assert order["amount"] == 550

    @skip_no_key
    def test_create_order_zero_amount_fails(self):
        with pytest.raises(Exception):
            create_razorpay_order(amount=0, currency="INR")

    @skip_no_key
    def test_create_and_fetch_order(self):
        order = create_razorpay_order(amount=2.0, currency="INR", receipt="test_fetch_001")
        client = get_razorpay_client()
        fetched = client.order.fetch(order["id"])
        assert fetched["id"] == order["id"]
        assert fetched["amount"] == 200
        assert fetched["status"] == "created"

    @skip_no_key
    def test_get_razorpay_client_returns_authenticated_client(self):
        client = get_razorpay_client()
        resp = client.order.all()
        assert "items" in resp
        assert isinstance(resp["items"], list)

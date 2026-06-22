from unittest.mock import patch
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.cart import Cart, CartItem
from app.models.user import User
from app.models.address import Address
from app.models.category import Category
from app.core.security import create_access_token, get_password_hash
from tests.conftest import TestingSessionLocal


SAMPLE_PRODUCT = {
    "title": "Webhook Test Product",
    "description": "desc",
    "price": 29.99,
    "discountPercentage": 10.0,
    "rating": 4.5,
    "stock": 10,
    "tags": ["test"],
    "brand": "Brand",
    "sku": "WHK-TST-001",
    "weight": 1.5,
    "dimensions": {"width": 10.0, "height": 5.0, "depth": 3.0},
    "warrantyInformation": "1 year",
    "shippingInformation": "Ships",
    "availabilityStatus": "In Stock",
    "reviews": [],
    "returnPolicy": "30 days",
    "minimumOrderQuantity": 1,
    "meta": {"createdAt": "2024-01-01T00:00:00Z", "updatedAt": "2024-01-01T00:00:00Z", "barcode": "123", "qrCode": "https://example.com/qr"},
    "images": ["https://example.com/img.jpg"],
    "thumbnail": "https://example.com/thumb.jpg",
}


def _make_webhook_session():
    return TestingSessionLocal()


def _create_user(db: Session, email: str = "wh@test.com") -> User:
    user = User(email=email, hashed_password=get_password_hash("pw"), is_active=True, is_verified=True, role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_category(db: Session) -> int:
    cat = Category(name="wh-cat")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat.id


def _create_product(db: Session, cat_id: int, overrides: dict | None = None) -> Product:
    data = {**SAMPLE_PRODUCT}
    if overrides:
        data.update(overrides)
    product = Product(
        title=data["title"], description=data["description"], category_id=cat_id,
        price=data["price"], discount_percentage=data["discountPercentage"],
        rating=data["rating"], stock=data["stock"], tags=data["tags"],
        brand=data.get("brand"), sku=data["sku"], weight=data["weight"],
        dimensions=data["dimensions"], warranty_information=data["warrantyInformation"],
        shipping_information=data["shippingInformation"],
        availability_status=data["availabilityStatus"], reviews=data["reviews"],
        return_policy=data["returnPolicy"], minimum_order_quantity=data["minimumOrderQuantity"],
        meta=data["meta"], images=data["images"], thumbnail=data["thumbnail"],
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _create_address(db: Session, user_id: int) -> Address:
    addr = Address(user_id=user_id, label="Home", street="123 St", city="City",
                   state="State", pincode="400001", country="India", is_default=True, address_type="both")
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def _add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 2):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
    db.add(item)
    db.commit()


def _create_pending_order(db: Session, user_id: int, product_id: int,
                          razorpay_order_id: str = "rzp_test_wh_001") -> Order:
    order = Order(
        user_id=user_id, status=OrderStatus.PENDING_PAYMENT,
        shipping_name="Test", shipping_phone="123",
        shipping_address_line_1="Addr", shipping_city="City",
        shipping_state="State", shipping_country="India", shipping_pincode="400001",
        subtotal=59.98, total=59.98, razorpay_order_id=razorpay_order_id,
    )
    db.add(order)
    db.flush()
    from app.models.order import OrderItem
    item = OrderItem(order_id=order.id, product_id=product_id,
                     product_name="Webhook Test Product", product_price=29.99,
                     quantity=2, subtotal=59.98)
    db.add(item)
    db.commit()
    db.refresh(order)
    return order


def _user_token(db: Session, user: User) -> dict:
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


class TestWebhookRazorpay:
    def _webhook_payload(self, event: str = "payment.captured",
                         order_id: str = "rzp_test_wh_001",
                         payment_id: str = "rzp_pay_wh_001") -> str:
        return json.dumps({
            "event": event,
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "order_id": order_id,
                    }
                }
            }
        })

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    def test_invalid_signature_returns_400(self, mock_verify, client: TestClient, db: Session):
        mock_verify.return_value = False
        resp = client.post("/api/v1/webhooks/razorpay", content="{}", headers={"x-razorpay-signature": "bad"})
        assert resp.status_code == 400
        assert "signature" in resp.json()["detail"].lower()

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    def test_non_payment_captured_event_returns_ok(self, mock_verify, client: TestClient, db: Session):
        mock_verify.return_value = True
        payload = self._webhook_payload(event="payment.failed")
        resp = client.post("/api/v1/webhooks/razorpay", content=payload, headers={"x-razorpay-signature": "sig"})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    @patch("app.api.v1.endpoints.webhooks.SessionLocal")
    def test_order_not_found_returns_ignored(self, mock_session_local, mock_verify,
                                             client: TestClient, db: Session):
        mock_verify.return_value = True
        mock_session_local.side_effect = _make_webhook_session
        payload = self._webhook_payload(order_id="rzp_test_nonexistent")
        resp = client.post("/api/v1/webhooks/razorpay", content=payload, headers={"x-razorpay-signature": "sig"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"
        assert resp.json()["reason"] == "order_not_found"

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    @patch("app.api.v1.endpoints.webhooks.SessionLocal")
    def test_order_not_pending_returns_ignored(self, mock_session_local, mock_verify,
                                              client: TestClient, db: Session):
        mock_verify.return_value = True
        mock_session_local.side_effect = _make_webhook_session

        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        from app.api.v1.endpoints.orders import create_razorpay_order
        with patch("app.api.v1.endpoints.orders.create_razorpay_order") as mock_create:
            mock_create.return_value = {"id": "rzp_test_already_paid"}
            client.post("/api/v1/orders/create-payment",
                        json={"address_id": address.id}, headers=_user_token(db, user))

        order = db.query(Order).filter(Order.razorpay_order_id == "rzp_test_already_paid").first()
        order.status = OrderStatus.PAID
        db.commit()

        payload = self._webhook_payload(order_id="rzp_test_already_paid")
        resp = client.post("/api/v1/webhooks/razorpay", content=payload,
                           headers={"x-razorpay-signature": "sig"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"
        assert "order_status_PAID" in resp.json()["reason"]

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    @patch("app.api.v1.endpoints.webhooks.SessionLocal")
    def test_successful_payment_captured_changes_status_to_paid(
            self, mock_session_local, mock_verify, client: TestClient, db: Session):
        mock_verify.return_value = True
        mock_session_local.side_effect = _make_webhook_session

        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10})
        _create_pending_order(db, user.id, product.id, razorpay_order_id="rzp_test_wh_success")

        payload = self._webhook_payload(order_id="rzp_test_wh_success", payment_id="rzp_pay_wh_001")
        resp = client.post("/api/v1/webhooks/razorpay", content=payload,
                           headers={"x-razorpay-signature": "sig"})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        db.expire_all()
        order = db.query(Order).filter(Order.razorpay_order_id == "rzp_test_wh_success").first()
        assert order.status == OrderStatus.PAID
        assert order.razorpay_payment_id == "rzp_pay_wh_001"
        assert order.payment_status == "paid"

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    @patch("app.api.v1.endpoints.webhooks.SessionLocal")
    def test_stock_deducted_on_webhook(self, mock_session_local, mock_verify,
                                       client: TestClient, db: Session):
        mock_verify.return_value = True
        mock_session_local.side_effect = _make_webhook_session

        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10})
        _create_pending_order(db, user.id, product.id, razorpay_order_id="rzp_test_wh_stock")

        old_stock = product.stock
        payload = self._webhook_payload(order_id="rzp_test_wh_stock")
        client.post("/api/v1/webhooks/razorpay", content=payload,
                    headers={"x-razorpay-signature": "sig"})

        db.refresh(product)
        assert product.stock == old_stock - 2

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    @patch("app.api.v1.endpoints.webhooks.SessionLocal")
    def test_cart_cleared_on_webhook(self, mock_session_local, mock_verify,
                                     client: TestClient, db: Session):
        mock_verify.return_value = True
        mock_session_local.side_effect = _make_webhook_session

        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        _add_to_cart(db, user.id, product.id)
        _create_pending_order(db, user.id, product.id, razorpay_order_id="rzp_test_wh_cart")

        payload = self._webhook_payload(order_id="rzp_test_wh_cart")
        client.post("/api/v1/webhooks/razorpay", content=payload,
                    headers={"x-razorpay-signature": "sig"})

        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        assert cart is not None
        assert len(cart.items) == 0

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    @patch("app.api.v1.endpoints.webhooks.SessionLocal")
    def test_webhook_insufficient_stock_does_not_deduct(
            self, mock_session_local, mock_verify, client: TestClient, db: Session):
        mock_verify.return_value = True
        mock_session_local.side_effect = _make_webhook_session

        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 1})
        _create_pending_order(db, user.id, product.id, razorpay_order_id="rzp_test_wh_lowstock")

        payload = self._webhook_payload(order_id="rzp_test_wh_lowstock")
        client.post("/api/v1/webhooks/razorpay", content=payload,
                    headers={"x-razorpay-signature": "sig"})

        db.refresh(product)
        assert product.stock == 1

    @patch("app.api.v1.endpoints.webhooks.verify_webhook_signature")
    def test_missing_signature_header(self, mock_verify, client: TestClient, db: Session):
        mock_verify.return_value = False
        resp = client.post("/api/v1/webhooks/razorpay", content="{}")
        assert resp.status_code == 400



from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderStatus

from app.core.security import create_access_token, get_password_hash


SAMPLE_PRODUCT = {
    "title": "Order Test Product",
    "description": "A product for order testing",
    "price": 29.99,
    "discountPercentage": 10.0,
    "rating": 4.5,
    "stock": 50,
    "tags": ["test"],
    "brand": "TestBrand",
    "sku": "ORD-TST-001",
    "weight": 1.5,
    "dimensions": {"width": 10.0, "height": 5.0, "depth": 3.0},
    "warrantyInformation": "1 year warranty",
    "shippingInformation": "Ships in 3-5 days",
    "availabilityStatus": "In Stock",
    "reviews": [],
    "returnPolicy": "30 days return",
    "minimumOrderQuantity": 1,
    "meta": {
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "barcode": "123456789",
        "qrCode": "https://example.com/qr",
    },
    "images": ["https://example.com/img1.jpg"],
    "thumbnail": "https://example.com/thumb.jpg",
}


def _create_user(db: Session, email: str = "orderuser@test.com", name: str | None = None) -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash("pw123"),
        is_active=True,
        is_verified=True,
        role="user",
        first_name=name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _user_token(user: User) -> dict:
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def _create_category(db: Session, name: str = "order-cat") -> int:
    cat = Category(name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat.id


def _create_product(
    db: Session, cat_id: int, overrides: dict | None = None,
) -> Product:
    data = {**SAMPLE_PRODUCT}
    if overrides:
        data.update(overrides)
    product = Product(
        title=data["title"],
        description=data["description"],
        category_id=cat_id,
        price=data["price"],
        discount_percentage=data["discountPercentage"],
        rating=data["rating"],
        stock=data["stock"],
        tags=data["tags"],
        brand=data.get("brand"),
        sku=data["sku"],
        weight=data["weight"],
        dimensions=data["dimensions"],
        warranty_information=data["warrantyInformation"],
        shipping_information=data["shippingInformation"],
        availability_status=data["availabilityStatus"],
        reviews=data["reviews"],
        return_policy=data["returnPolicy"],
        minimum_order_quantity=data["minimumOrderQuantity"],
        meta=data["meta"],
        images=data["images"],
        thumbnail=data["thumbnail"],
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _create_address(db: Session, user_id: int) -> Address:
    addr = Address(
        user_id=user_id,
        label="Home",
        street="123 Test St",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        country="India",
        is_default=True,
        address_type="both",
    )
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
    product = db.query(Product).filter(Product.id == product_id).first()
    product_price = round(product.price * (1 - product.discount_percentage / 100), 2) if product else 0
    item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, product_price=product_price)
    db.add(item)
    db.commit()


class TestCreatePayment:
    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_success(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db, name="John")
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10, "discountPercentage": 0})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)
        eff_price = round(product.price * (1 - product.discount_percentage / 100), 2)

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["razorpay_order_id"] == "rzp_test_order_123"
        assert data["amount"] == round(2 * eff_price, 2)
        assert data["currency"] == "INR"
        assert "order_id" not in data

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_empty_cart_returns_400(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        address = _create_address(db, user.id)

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_invalid_address_returns_404(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        _add_to_cart(db, user.id, product.id)

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": 99999},
            headers=headers,
        )
        assert resp.status_code == 404

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_address_belonging_to_another_user_returns_404(
        self, mock_create_order, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user1 = _create_user(db, "user1@test.com")
        user2 = _create_user(db, "user2@test.com")
        headers2 = _user_token(user2)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        _add_to_cart(db, user2.id, product.id)

        address = _create_address(db, user1.id)

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers2,
        )
        assert resp.status_code == 404

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_insufficient_stock_returns_400(
        self, mock_create_order, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 1})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=5)

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "stock" in resp.json()["detail"].lower()

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_does_not_deduct_stock(
        self, mock_create_order, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=3)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        db.refresh(product)
        assert product.stock == 10  # Stock NOT deducted

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_does_not_clear_cart(
        self, mock_create_order, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        cart_resp = client.get("/api/v1/cart", headers=headers)
        assert len(cart_resp.json()["items"]) > 0  # Cart NOT cleared

    @patch("app.services.order_service.create_razorpay_order")
    def test_order_item_has_product_snapshot(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"price": 15.99, "discountPercentage": 0})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        with patch("app.services.order_service.verify_payment_signature", return_value=True):
            verify_resp = client.post(
                "/api/v1/orders/verify-payment",
                json={
                    "razorpay_order_id": "rzp_test_order_123",
                    "razorpay_payment_id": "rzp_pay_test_456",
                    "razorpay_signature": "sig",
                },
                headers=headers,
            )
        assert verify_resp.status_code == 200
        order_id = verify_resp.json()["id"]

        order_resp = client.get(f"/api/v1/orders/{order_id}", headers=headers)
        assert order_resp.status_code == 200
        item = order_resp.json()["items"][0]
        assert item["product_id"] == product.id
        assert item["product_name"] == product.title
        assert item["product_price"] == 15.99
        assert item["quantity"] == 2
        assert item["subtotal"] == 31.98

    @patch("app.services.order_service.create_razorpay_order")
    def test_order_subtotal_matches_cart_total(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        p1 = _create_product(db, cat_id, {"sku": "MULTI-1", "price": 10.0, "title": "P1", "discountPercentage": 0})
        p2 = _create_product(db, cat_id, {"sku": "MULTI-2", "price": 20.0, "title": "P2", "discountPercentage": 0})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, p1.id, quantity=3)
        _add_to_cart(db, user.id, p2.id, quantity=2)

        cart_resp = client.get("/api/v1/cart", headers=headers)
        cart_total = cart_resp.json()["total"]

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["amount"] == cart_total
        assert resp.json()["amount"] == round(3 * 10.0 + 2 * 20.0, 2)

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_razorpay_failure_returns_502(
        self, mock_create_order, client: TestClient, db: Session
    ):
        mock_create_order.side_effect = Exception("Razorpay API error")
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        assert resp.status_code == 502
        assert "razorpay" in resp.json()["detail"].lower()

    @patch("app.services.order_service.create_razorpay_order")
    def test_create_payment_shipping_name_falls_back_to_email(
        self, mock_create_order, client: TestClient, db: Session
    ):
        """When user has no first_name/last_name, shipping_name falls back to email."""
        mock_create_order.return_value = {"id": "rzp_test_order_nameless"}
        user = _create_user(db, email="nameless@test.com")
        user.first_name = None
        user.last_name = None
        db.commit()
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        with patch("app.services.order_service.verify_payment_signature", return_value=True):
            verify_resp = client.post(
                "/api/v1/orders/verify-payment",
                json={
                    "razorpay_order_id": "rzp_test_order_nameless",
                    "razorpay_payment_id": "rzp_pay_test_456",
                    "razorpay_signature": "sig",
                },
                headers=headers,
            )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["shipping_name"] == "nameless@test.com"


class TestVerifyPayment:
    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_success(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True

        user = _create_user(db, name="John")
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)

        create_resp = client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        assert create_resp.status_code == 201

        resp = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_order_123",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "valid_signature",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PAID"
        assert data["razorpay_payment_id"] == "rzp_pay_test_456"

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_deducts_stock(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=3)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_order_123",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "valid_signature",
            },
            headers=headers,
        )

        db.refresh(product)
        assert product.stock == 7  # Stock deducted after verify

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_clears_cart(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )
        client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_order_123",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "valid_signature",
            },
            headers=headers,
        )

        cart_resp = client.get("/api/v1/cart", headers=headers)
        assert cart_resp.json()["items"] == []

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_invalid_signature(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = False

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        resp = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_order_123",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "bad_signature",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert "signature" in resp.json()["detail"].lower()

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_wrong_order(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        resp = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_wrong_order",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "sig",
            },
            headers=headers,
        )
        assert resp.status_code == 404

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_insufficient_stock(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 5})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        product.stock = 0
        db.commit()

        resp = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_order_123",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "sig",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert "stock" in resp.json()["detail"].lower()

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_order_already_paid_returns_400(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_already_paid"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        # First verify succeeds
        resp1 = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_already_paid",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "sig",
            },
            headers=headers,
        )
        assert resp1.status_code == 200

        # Second verify should fail (pending payment already consumed)
        resp2 = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_already_paid",
                "razorpay_payment_id": "rzp_pay_test_789",
                "razorpay_signature": "sig",
            },
            headers=headers,
        )
        assert resp2.status_code == 404

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_product_deleted_returns_400(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_prod_del"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10, "sku": "PROD-DEL"})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        db.execute(text("PRAGMA foreign_keys=OFF"))
        db.delete(product)
        db.commit()
        db.execute(text("PRAGMA foreign_keys=ON"))

        resp = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_prod_del",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "sig",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert "no longer exists" in resp.json()["detail"]

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_verify_payment_cart_is_none(
        self, mock_create_order, mock_verify, client: TestClient, db: Session
    ):
        mock_create_order.return_value = {"id": "rzp_test_no_cart"}
        mock_verify.return_value = True

        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 10, "sku": "NO-CART"})
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id, quantity=2)

        client.post(
            "/api/v1/orders/create-payment",
            json={"address_id": address.id},
            headers=headers,
        )

        db.execute(text("PRAGMA foreign_keys=OFF"))
        db.query(Cart).delete()
        db.commit()
        db.execute(text("PRAGMA foreign_keys=ON"))

        resp = client.post(
            "/api/v1/orders/verify-payment",
            json={
                "razorpay_order_id": "rzp_test_no_cart",
                "razorpay_payment_id": "rzp_pay_test_456",
                "razorpay_signature": "sig",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()


class TestListOrders:
    @patch("app.services.order_service.create_razorpay_order")
    def test_list_returns_own_orders_only(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user1 = _create_user(db, "list1@test.com", "User One")
        user2 = _create_user(db, "list2@test.com", "User Two")
        cat_id = _create_category(db)

        p1 = _create_product(db, cat_id, {"sku": "LST-1"})
        addr1 = _create_address(db, user1.id)
        _add_to_cart(db, user1.id, p1.id)
        client.post("/api/v1/orders/create-payment", json={"address_id": addr1.id}, headers=_user_token(user1))
        with patch("app.services.order_service.verify_payment_signature", return_value=True):
            client.post("/api/v1/orders/verify-payment", json={"razorpay_order_id": "rzp_test_order_123", "razorpay_payment_id": "rzp_pay", "razorpay_signature": "sig"}, headers=_user_token(user1))

        p2 = _create_product(db, cat_id, {"sku": "LST-2", "title": "P2"})
        addr2 = _create_address(db, user2.id)
        _add_to_cart(db, user2.id, p2.id)
        client.post("/api/v1/orders/create-payment", json={"address_id": addr2.id}, headers=_user_token(user2))
        with patch("app.services.order_service.verify_payment_signature", return_value=True):
            client.post("/api/v1/orders/verify-payment", json={"razorpay_order_id": "rzp_test_order_123", "razorpay_payment_id": "rzp_pay", "razorpay_signature": "sig"}, headers=_user_token(user2))

        resp1 = client.get("/api/v1/orders", headers=_user_token(user1))
        assert len(resp1.json()) == 1
        assert resp1.json()[0]["shipping_name"] == "User One"

        resp2 = client.get("/api/v1/orders", headers=_user_token(user2))
        assert len(resp2.json()) == 1
        assert resp2.json()[0]["shipping_name"] == "User Two"

    @patch("app.services.order_service.create_razorpay_order")
    def test_list_orders_newest_first(self, mock_create_order, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        p1 = _create_product(db, cat_id, {"sku": "NEW-1"})
        p2 = _create_product(db, cat_id, {"sku": "NEW-2", "title": "P2"})
        addr = _create_address(db, user.id)

        _add_to_cart(db, user.id, p1.id)
        client.post("/api/v1/orders/create-payment", json={"address_id": addr.id}, headers=headers)
        with patch("app.services.order_service.verify_payment_signature", return_value=True):
            resp1 = client.post("/api/v1/orders/verify-payment", json={"razorpay_order_id": "rzp_test_order_123", "razorpay_payment_id": "rzp_pay", "razorpay_signature": "sig"}, headers=headers)
        order1_id = resp1.json()["id"]

        _add_to_cart(db, user.id, p2.id)
        client.post("/api/v1/orders/create-payment", json={"address_id": addr.id}, headers=headers)
        with patch("app.services.order_service.verify_payment_signature", return_value=True):
            resp2 = client.post("/api/v1/orders/verify-payment", json={"razorpay_order_id": "rzp_test_order_123", "razorpay_payment_id": "rzp_pay", "razorpay_signature": "sig"}, headers=headers)
        order2_id = resp2.json()["id"]

        orders = client.get("/api/v1/orders", headers=headers).json()
        assert len(orders) == 2
        assert orders[0]["id"] > orders[1]["id"]


class TestGetOrder:
    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_get_own_order(self, mock_create_order, mock_verify, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True
        user = _create_user(db)
        headers = _user_token(user)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)
        _add_to_cart(db, user.id, product.id)

        client.post("/api/v1/orders/create-payment", json={"address_id": address.id}, headers=headers)
        verify_resp = client.post(
            "/api/v1/orders/verify-payment",
            json={"razorpay_order_id": "rzp_test_order_123", "razorpay_payment_id": "rzp_pay", "razorpay_signature": "sig"},
            headers=headers,
        )
        order_id = verify_resp.json()["id"]

        resp = client.get(f"/api/v1/orders/{order_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    @patch("app.services.order_service.verify_payment_signature")
    @patch("app.services.order_service.create_razorpay_order")
    def test_get_other_users_order_returns_404(self, mock_create_order, mock_verify, client: TestClient, db: Session):
        mock_create_order.return_value = {"id": "rzp_test_order_123"}
        mock_verify.return_value = True
        user1 = _create_user(db, "get1@test.com")
        user2 = _create_user(db, "get2@test.com")
        cat_id = _create_category(db)

        product = _create_product(db, cat_id)
        address = _create_address(db, user1.id)
        _add_to_cart(db, user1.id, product.id)

        client.post("/api/v1/orders/create-payment", json={"address_id": address.id}, headers=_user_token(user1))
        verify_resp = client.post(
            "/api/v1/orders/verify-payment",
            json={"razorpay_order_id": "rzp_test_order_123", "razorpay_payment_id": "rzp_pay", "razorpay_signature": "sig"},
            headers=_user_token(user1),
        )
        order_id = verify_resp.json()["id"]

        resp = client.get(f"/api/v1/orders/{order_id}", headers=_user_token(user2))
        assert resp.status_code == 404

    def test_get_nonexistent_order_returns_404(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/orders/99999", headers=_user_token(user))
        assert resp.status_code == 404




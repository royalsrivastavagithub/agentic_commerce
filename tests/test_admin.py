from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.review import Review
from app.core.security import create_access_token, get_password_hash

SAMPLE_PRODUCT = {
    "title": "Admin Test Product",
    "description": "desc",
    "price": 100.0,
    "discountPercentage": 10.0,
    "rating": 4.0,
    "stock": 50,
    "tags": ["test"],
    "brand": "Brand",
    "sku": "ADM-TST-001",
    "weight": 1.0,
    "dimensions": {"width": 10.0, "height": 5.0, "depth": 3.0},
    "warrantyInformation": "1 year",
    "shippingInformation": "Ships in days",
    "availabilityStatus": "In Stock",
    "returnPolicy": "30 days",
    "minimumOrderQuantity": 1,
    "meta": {"createdAt": "2024-01-01T00:00:00Z", "updatedAt": "2024-01-01T00:00:00Z", "barcode": "123", "qrCode": "https://example.com/qr"},
    "images": ["https://example.com/img.jpg"],
    "thumbnail": "https://example.com/thumb.jpg",
}


def _create_admin(db: Session) -> User:
    admin = User(
        email="admintest@test.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_verified=True,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _create_user(db: Session, email: str = "testuser@test.com", role: str = "user") -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash("pw123"),
        is_active=True,
        is_verified=True,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id, role=user.role)}"}


def _create_category(db: Session, name: str = "admin-cat") -> int:
    cat = Category(name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat.id


def _create_product(db: Session, cat_id: int, overrides: dict | None = None) -> Product:
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
        user_id=user_id, label="Home", street="123 St", city="City",
        state="State", pincode="400001", country="Country",
        is_default=True, address_type="both",
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def _create_order(db: Session, user_id: int, product_id: int, total: float = 200.0) -> Order:
    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING,
        shipping_name="Test", shipping_phone="123",
        shipping_address_line_1="Addr", shipping_city="City",
        shipping_state="State", shipping_country="Country",
        shipping_pincode="400001",
        subtotal=total, total=total,
    )
    db.add(order)
    db.flush()
    item = OrderItem(
        order_id=order.id, product_id=product_id,
        product_name="P", product_price=100.0, quantity=2, subtotal=200.0,
    )
    db.add(item)
    db.commit()
    db.refresh(order)
    return order


# ─── Admin Users ────────────────────────────────────────────────────

class TestAdminUsers:
    def test_list_users_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/users", headers=_token(user))
        assert resp.status_code == 403

    def test_list_users_pagination(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        for i in range(5):
            _create_user(db, f"u{i}@test.com")

        resp = client.get("/api/v1/admin/users?page=1&per_page=2", headers=_token(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_users_search(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        _create_user(db, "alice@test.com")
        _create_user(db, "bob@test.com")

        resp = client.get("/api/v1/admin/users?search=alice", headers=_token(admin))
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["email"] == "alice@test.com"

    def test_get_user_detail(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        _create_order(db, user.id, product.id, total=150.0)

        resp = client.get(f"/api/v1/admin/users/{user.id}", headers=_token(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "testuser@test.com"
        assert data["order_count"] == 1
        assert data["total_spent"] == 150.0

    def test_get_user_not_found(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.get("/api/v1/admin/users/99999", headers=_token(admin))
        assert resp.status_code == 404

    def test_update_user(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)

        resp = client.patch(
            f"/api/v1/admin/users/{user.id}",
            json={"first_name": "Updated", "is_active": False},
            headers=_token(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"
        assert resp.json()["is_active"] is False

    def test_update_user_not_found(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.patch("/api/v1/admin/users/99999", json={"first_name": "X"}, headers=_token(admin))
        assert resp.status_code == 404

    def test_delete_user(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db, "delete@test.com")

        resp = client.delete(f"/api/v1/admin/users/{user.id}", headers=_token(admin))
        assert resp.status_code == 204

        # verify deleted
        assert db.query(User).filter(User.id == user.id).first() is None

    def test_delete_self_forbidden(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.delete(f"/api/v1/admin/users/{admin.id}", headers=_token(admin))
        assert resp.status_code == 400

    def test_delete_user_not_found(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.delete("/api/v1/admin/users/99999", headers=_token(admin))
        assert resp.status_code == 404

    def test_update_user_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.patch(f"/api/v1/admin/users/{user.id}", json={"first_name": "X"}, headers=_token(user))
        assert resp.status_code == 403

    def test_delete_user_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.delete(f"/api/v1/admin/users/{user.id}", headers=_token(user))
        assert resp.status_code == 403


# ─── Admin Reviews ──────────────────────────────────────────────────

class TestAdminReviews:
    def test_list_all_reviews_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/reviews", headers=_token(user))
        assert resp.status_code == 403

    def test_list_all_reviews(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        review = Review(user_id=user.id, product_id=product.id, rating=4, comment="Great")
        db.add(review)
        db.commit()

        resp = client.get("/api/v1/admin/reviews", headers=_token(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["comment"] == "Great"

    def test_list_reviews_filter_by_product(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        p1 = _create_product(db, cat_id, {"sku": "FLT-1"})
        p2 = _create_product(db, cat_id, {"sku": "FLT-2", "title": "P2"})
        db.add(Review(user_id=user.id, product_id=p1.id, rating=3, comment="OK"))
        db.add(Review(user_id=user.id, product_id=p2.id, rating=5, comment="Best"))
        db.commit()

        resp = client.get(f"/api/v1/admin/reviews?product_id={p1.id}", headers=_token(admin))
        assert len(resp.json()) == 1

    def test_delete_review_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        review = Review(user_id=user.id, product_id=product.id, rating=3, comment="X")
        db.add(review)
        db.commit()

        resp = client.delete(f"/api/v1/admin/reviews/{review.id}", headers=_token(user))
        assert resp.status_code == 403

    def test_delete_review(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        review = Review(user_id=user.id, product_id=product.id, rating=4, comment="Great")
        db.add(review)
        db.commit()

        resp = client.delete(f"/api/v1/admin/reviews/{review.id}", headers=_token(admin))
        assert resp.status_code == 204
        assert db.query(Review).filter(Review.id == review.id).first() is None

    def test_delete_review_not_found(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.delete("/api/v1/admin/reviews/99999", headers=_token(admin))
        assert resp.status_code == 404

    def test_delete_review_recalculates_rating(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user1 = _create_user(db, "rater1@test.com")
        user2 = _create_user(db, "rater2@test.com")
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"sku": "RRC-1", "rating": 0})
        r1 = Review(user_id=user1.id, product_id=product.id, rating=5, comment="Great")
        r2 = Review(user_id=user2.id, product_id=product.id, rating=1, comment="Bad")
        db.add(r1)
        db.add(r2)
        db.commit()

        client.delete(f"/api/v1/admin/reviews/{r2.id}", headers=_token(admin))
        db.refresh(product)
        assert product.rating == 5.0
        assert product.review_count == 1


# ─── Admin Dashboard ────────────────────────────────────────────────

class TestAdminDashboard:
    def test_summary_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/dashboard/summary", headers=_token(user))
        assert resp.status_code == 403

    def test_summary_empty(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.get("/api/v1/admin/dashboard/summary", headers=_token(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] == 1  # just the admin
        assert data["total_products"] == 0
        assert data["total_orders"] == 0
        assert data["total_revenue"] == 0.0
        assert data["avg_order_value"] == 0.0
        assert data["low_stock_count"] == 0

    def test_summary_with_data(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 3})
        address = _create_address(db, user.id)

        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=2))
        db.commit()

        client.post("/api/v1/orders", json={"address_id": address.id}, headers=_token(user))

        resp = client.get("/api/v1/admin/dashboard/summary", headers=_token(admin))
        data = resp.json()
        assert data["total_users"] == 2
        assert data["total_products"] == 1
        assert data["total_orders"] == 1
        assert data["total_revenue"] == 200.0
        assert data["avg_order_value"] == 200.0
        assert data["low_stock_count"] == 1
        assert data["orders_by_status"]["PENDING"] == 1

    def test_top_products_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/dashboard/top-products", headers=_token(user))
        assert resp.status_code == 403

    def test_top_products(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        p = _create_product(db, cat_id)
        address = _create_address(db, user.id)

        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=p.id, quantity=3))
        db.commit()

        client.post("/api/v1/orders", json={"address_id": address.id}, headers=_token(user))

        resp = client.get("/api/v1/admin/dashboard/top-products", headers=_token(admin))
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == p.id
        assert data[0]["total_quantity"] == 3

    def test_recent_orders_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/dashboard/recent-orders", headers=_token(user))
        assert resp.status_code == 403

    def test_recent_orders(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        address = _create_address(db, user.id)

        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
        db.commit()

        client.post("/api/v1/orders", json={"address_id": address.id}, headers=_token(user))

        resp = client.get("/api/v1/admin/dashboard/recent-orders", headers=_token(admin))
        data = resp.json()
        assert len(data) == 1
        assert data[0]["user_email"] == "testuser@test.com"

    def test_recent_users_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/dashboard/recent-users", headers=_token(user))
        assert resp.status_code == 403

    def test_recent_users(self, client: TestClient, db: Session):
        admin = _create_admin(db)
        resp = client.get("/api/v1/admin/dashboard/recent-users", headers=_token(admin))
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["email"] == "admintest@test.com"

    def test_revenue_over_time_requires_admin(self, client: TestClient, db: Session):
        user = _create_user(db)
        resp = client.get("/api/v1/admin/dashboard/revenue-over-time", headers=_token(user))
        assert resp.status_code == 403

    def test_revenue_over_time(self, client: TestClient, db: Session):
        from datetime import timedelta

        admin = _create_admin(db)
        user = _create_user(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        now = datetime.now(timezone.utc)
        for days_ago, total in [(10, 100.0), (5, 200.0), (1, 300.0)]:
            order = _create_order(db, user.id, product.id, total=total)
            order.created_at = now - timedelta(days=days_ago)
            db.commit()

        resp = client.get("/api/v1/admin/dashboard/revenue-over-time?days=30", headers=_token(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        total_rev = sum(d["revenue"] for d in data)
        assert total_rev == 600.0

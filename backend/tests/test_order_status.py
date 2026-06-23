"""Tests for order status transition business logic."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.core.security import create_access_token, get_password_hash


def _create_admin(db: Session) -> tuple[User, dict]:
    admin = User(
        email="admin-order-status@test.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_verified=True,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    token = create_access_token(subject=admin.id, role=admin.role)
    return admin, {"Authorization": f"Bearer {token}"}


def _create_order(db: Session, status: OrderStatus = OrderStatus.PAID) -> tuple[Order, int]:
    user = User(
        email="order-status-user@test.com",
        hashed_password="x",
        is_active=True,
        is_verified=True,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    cat = Category(name="order-status-cat")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    product = Product(
        title="Status Test Product",
        description="test",
        category_id=cat.id,
        price=10.0,
        discount_percentage=0,
        rating=0,
        review_count=0,
        stock=10,
        tags=[],
        sku=f"STATUS-{status.value}",
        weight=1,
        dimensions={"width": 1, "height": 1, "depth": 1},
        warranty_information="1y",
        shipping_information="fast",
        availability_status="In Stock",
        return_policy="30d",
        minimum_order_quantity=1,
        meta={"createdAt": "", "updatedAt": "", "barcode": "", "qrCode": ""},
        images=[],
        thumbnail="https://example.com/thumb.jpg",
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    order = Order(
        user_id=user.id,
        status=status,
        shipping_name="T", shipping_phone="0",
        shipping_address_line_1="1 St", shipping_city="C",
        shipping_state="S", shipping_country="India", shipping_pincode="000000",
        subtotal=10.0, total=10.0,
    )
    db.add(order)
    db.flush()

    item = OrderItem(
        order_id=order.id, product_id=product.id,
        product_name="P", product_price=10.0, quantity=1, subtotal=10.0,
    )
    db.add(item)
    db.commit()
    db.refresh(order)

    return order, user.id


class TestOrderStatusTransitions:
    def test_paid_to_shipped_allowed(self, client: TestClient, db: Session):
        _, headers = _create_admin(db)
        order, _ = _create_order(db, OrderStatus.PAID)
        resp = client.patch(
            f"/api/v1/admin/orders/{order.id}/status",
            json={"status": "SHIPPED"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "SHIPPED"

    def test_shipped_to_delivered_allowed(self, client: TestClient, db: Session):
        _, headers = _create_admin(db)
        order, _ = _create_order(db, OrderStatus.SHIPPED)
        resp = client.patch(
            f"/api/v1/admin/orders/{order.id}/status",
            json={"status": "DELIVERED"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "DELIVERED"

    def test_invalid_status_value_returns_422(self, client: TestClient, db: Session):
        _, headers = _create_admin(db)
        order, _ = _create_order(db, OrderStatus.PAID)
        resp = client.patch(
            f"/api/v1/admin/orders/{order.id}/status",
            json={"status": "INVALID_STATUS"},
            headers=headers,
        )
        assert resp.status_code == 422

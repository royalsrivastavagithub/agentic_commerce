from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.core.security import create_access_token


_cat_counter = 0

def _setup(db: Session, email: str = "review@test.com"):
    global _cat_counter
    _cat_counter += 1
    sku = f"REV-{_cat_counter:03d}"
    user = User(
        email=email,
        hashed_password="x",
        is_active=True,
        is_verified=True,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}

    cat = Category(name=f"review-cat-{_cat_counter}")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    product = Product(
        title="Review Product",
        description="test",
        category_id=cat.id,
        price=19.99,
        discount_percentage=0,
        rating=0,
        review_count=0,
        stock=10,
        tags=[],
        sku=sku,
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
        total=product.price,
        subtotal=product.price,
        status=OrderStatus.DELIVERED,
        shipping_name="Test",
        shipping_phone="0000000000",
        shipping_address_line_1="123 Test St",
        shipping_city="Test City",
        shipping_state="TS",
        shipping_country="India",
        shipping_pincode="000000",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.title,
        product_price=product.price,
        quantity=1,
        subtotal=product.price,
        thumbnail=product.thumbnail,
    )
    db.add(order_item)
    db.commit()

    return user, headers, product


class TestAuthz:
    def test_list_reviews_without_auth(self, client: TestClient, db: Session):
        _, _, product = _setup(db)
        resp = client.get(f"/api/v1/products/{product.id}/reviews")
        assert resp.status_code == 200  # public endpoint

    def test_create_review_without_auth_returns_401(self, client: TestClient, db: Session):
        _, _, product = _setup(db)
        resp = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 5, "comment": "Great!"},
        )
        assert resp.status_code == 401

    def test_update_review_without_auth_returns_401(self, client: TestClient):
        resp = client.put("/api/v1/reviews/1", json={"rating": 4})
        assert resp.status_code == 401

    def test_delete_review_without_auth_returns_401(self, client: TestClient):
        resp = client.delete("/api/v1/reviews/1")
        assert resp.status_code == 401


class TestCreateReview:
    def test_create_review(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)

        resp = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 5, "comment": "Excellent product!"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent product!"
        assert data["product_id"] == product.id
        assert data["user"]["id"] is not None
        assert "user" in data

    def test_cannot_review_without_purchase_returns_403(self, client: TestClient, db: Session):
        user = User(
            email="nopurchase@test.com",
            hashed_password="x",
            is_active=True,
            is_verified=True,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(subject=user.id, role=user.role)
        headers = {"Authorization": f"Bearer {token}"}

        cat = Category(name="nopurchase-cat")
        db.add(cat)
        db.commit()
        db.refresh(cat)

        product = Product(
            title="No Purchase Product",
            description="test",
            category_id=cat.id,
            price=10.0,
            discount_percentage=0,
            rating=0,
            review_count=0,
            stock=10,
            tags=[],
            sku="NOPURCHASE",
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

        resp = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Never bought this"},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_duplicate_review_returns_409(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 5, "comment": "Great!"},
            headers=headers,
        )
        resp = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 3, "comment": "Changed my mind"},
            headers=headers,
        )
        assert resp.status_code == 409

    def test_invalid_rating_returns_422(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        resp = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 6, "comment": "Too high"},
            headers=headers,
        )
        assert resp.status_code == 422

        resp2 = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 0, "comment": "Too low"},
            headers=headers,
        )
        assert resp2.status_code == 422

    def test_nonexistent_product_returns_404(self, client: TestClient, db: Session):
        _, headers, _ = _setup(db)
        resp = client.post(
            "/api/v1/products/99999/reviews",
            json={"rating": 4, "comment": "Nope"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_create_review_empty_comment(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        resp = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 3, "comment": ""},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["comment"] == ""


class TestRatingRecalculation:
    def test_rating_updates_after_create(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        assert product.rating == 0
        assert product.review_count == 0

        client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Good"},
            headers=headers,
        )

        db.refresh(product)
        assert product.rating == 4.0
        assert product.review_count == 1

    def test_rating_is_average_of_multiple_reviews(self, client: TestClient, db: Session):
        _, _, product = _setup(db)
        user2, headers2, _ = _setup(db, "review2@test.com")

        order2 = Order(
            user_id=user2.id, total=product.price, subtotal=product.price,
            status=OrderStatus.DELIVERED, shipping_name="T", shipping_phone="0",
            shipping_address_line_1="1 St", shipping_city="C", shipping_state="S",
            shipping_country="India", shipping_pincode="000000",
        )
        db.add(order2)
        db.commit()

        order_item2 = OrderItem(
            order_id=order2.id, product_id=product.id, product_name=product.title,
            product_price=product.price, quantity=1, subtotal=product.price,
            thumbnail=product.thumbnail,
        )
        db.add(order_item2)
        db.commit()

        client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 3, "comment": "ok"},
            headers=headers2,
        )

        user3 = User(
            email="review3@test.com",
            hashed_password="x",
            is_active=True,
            is_verified=True,
            role="user",
        )
        db.add(user3)
        db.commit()

        order3 = Order(
            user_id=user3.id, total=product.price, subtotal=product.price,
            status=OrderStatus.DELIVERED, shipping_name="T", shipping_phone="0",
            shipping_address_line_1="1 St", shipping_city="C", shipping_state="S",
            shipping_country="India", shipping_pincode="000000",
        )
        db.add(order3)
        db.commit()

        order_item3 = OrderItem(
            order_id=order3.id, product_id=product.id, product_name=product.title,
            product_price=product.price, quantity=1, subtotal=product.price,
            thumbnail=product.thumbnail,
        )
        db.add(order_item3)
        db.commit()

        headers3 = {"Authorization": f"Bearer {create_access_token(subject=user3.id, role=user3.role)}"}

        client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 5, "comment": "Great!"},
            headers=headers3,
        )

        db.refresh(product)
        assert product.rating == 4.0  # (3 + 5) / 2
        assert product.review_count == 2

    def test_rating_updates_after_update(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 2, "comment": "Bad"},
            headers=headers,
        ).json()

        client.put(
            f"/api/v1/reviews/{created['id']}",
            json={"rating": 5},
            headers=headers,
        )

        db.refresh(product)
        assert product.rating == 5.0

    def test_rating_updates_after_delete(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Nice"},
            headers=headers,
        ).json()

        client.delete(
            f"/api/v1/reviews/{created['id']}",
            headers=headers,
        )

        db.refresh(product)
        assert product.rating == 0
        assert product.review_count == 0


class TestUpdateReview:
    def test_update_own_review(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 3, "comment": "Average"},
            headers=headers,
        ).json()

        resp = client.put(
            f"/api/v1/reviews/{created['id']}",
            json={"rating": 4, "comment": "Actually pretty good"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["rating"] == 4
        assert resp.json()["comment"] == "Actually pretty good"

    def test_update_other_users_review_returns_404(self, client: TestClient, db: Session):
        u1, h1, product = _setup(db, "u1@test.com")
        u2, h2, _ = _setup(db, "u2@test.com")

        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Mine"},
            headers=h1,
        ).json()

        resp = client.put(
            f"/api/v1/reviews/{created['id']}",
            json={"rating": 1},
            headers=h2,
        )
        assert resp.status_code == 404

    def test_update_review_empty_comment(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Initial"},
            headers=headers,
        ).json()

        resp = client.put(
            f"/api/v1/reviews/{created['id']}",
            json={"comment": ""},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["comment"] == ""


class TestEmptyUpdateBody:
    def test_update_with_empty_body_returns_200(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Good"},
            headers=headers,
        ).json()
        resp = client.put(
            f"/api/v1/reviews/{created['id']}",
            json={},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["rating"] == 4
        assert resp.json()["comment"] == "Good"


class TestDeleteReview:
    def test_delete_own_review(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Good"},
            headers=headers,
        ).json()

        resp = client.delete(f"/api/v1/reviews/{created['id']}", headers=headers)
        assert resp.status_code == 204

    def test_delete_other_users_review_returns_404(self, client: TestClient, db: Session):
        u1, h1, product = _setup(db, "del1@test.com")
        u2, h2, _ = _setup(db, "del2@test.com")

        created = client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 4, "comment": "Mine"},
            headers=h1,
        ).json()

        resp = client.delete(f"/api/v1/reviews/{created['id']}", headers=h2)
        assert resp.status_code == 404


class TestListReviews:
    def test_list_reviews(self, client: TestClient, db: Session):
        _, headers, product = _setup(db)
        client.post(
            f"/api/v1/products/{product.id}/reviews",
            json={"rating": 5, "comment": "Love it"},
            headers=headers,
        )

        resp = client.get(f"/api/v1/products/{product.id}/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["rating"] == 5
        assert data[0]["user"]["email"] is not None

    def test_list_reviews_nonexistent_product_returns_404(self, client: TestClient):
        resp = client.get("/api/v1/products/99999/reviews")
        assert resp.status_code == 404

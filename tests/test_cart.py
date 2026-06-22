from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.core.security import create_access_token


SAMPLE_PRODUCT = {
    "title": "Cart Test Product",
    "description": "A product for cart testing",
    "price": 29.99,
    "discountPercentage": 10.0,
    "rating": 4.5,
    "stock": 50,
    "tags": ["test"],
    "brand": "TestBrand",
    "sku": "CART-TST-001",
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


def _create_user_token(db: Session, email: str = "cartuser@test.com") -> str:
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
    return create_access_token(subject=user.id, role=user.role)


def _create_admin_token(db: Session) -> str:
    admin = User(
        email="cartadmin@test.com",
        hashed_password="x",
        is_active=True,
        is_verified=True,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return create_access_token(subject=admin.id, role=admin.role)


def _create_category(db: Session, name: str = "cart-category") -> int:
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


class TestAuthz:
    def test_get_cart_without_auth_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/cart")
        assert resp.status_code == 401

    def test_add_item_without_auth_returns_401(self, client: TestClient):
        resp = client.post("/api/v1/cart/items", json={"product_id": 1})
        assert resp.status_code == 401

    def test_update_item_without_auth_returns_401(self, client: TestClient):
        resp = client.put("/api/v1/cart/items/1", json={"quantity": 2})
        assert resp.status_code == 401

    def test_remove_item_without_auth_returns_401(self, client: TestClient):
        resp = client.delete("/api/v1/cart/items/1")
        assert resp.status_code == 401

    def test_clear_cart_without_auth_returns_401(self, client: TestClient):
        resp = client.delete("/api/v1/cart")
        assert resp.status_code == 401


class TestEmptyCart:
    def test_empty_cart_returns_empty_items(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        resp = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestAddItem:
    def test_add_item_creates_cart_and_returns_item(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        resp = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["product_id"] == product.id
        assert data["quantity"] == 2
        assert data["product"]["id"] == product.id
        assert data["product"]["title"] == product.title
        assert data["product"]["price"] == product.price

        # Verify cart now has the item
        cart_resp = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"})
        assert len(cart_resp.json()["items"]) == 1

    def test_add_same_product_twice_increments_quantity(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["quantity"] == 4

    def test_add_item_exceeding_stock_returns_400(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 5})

        resp = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_add_nonexistent_product_returns_404(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        resp = client.post(
            "/api/v1/cart/items",
            json={"product_id": 99999, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_add_item_with_zero_quantity(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        resp = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["quantity"] == 0


class TestUpdateItem:
    def test_update_quantity(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        created = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        resp = client.put(
            f"/api/v1/cart/items/{created['id']}",
            json={"quantity": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 5

    def test_update_other_users_item_returns_404(self, client: TestClient, db: Session):
        token1 = _create_user_token(db, "user1@test.com")
        token2 = _create_user_token(db, "user2@test.com")
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        created = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token1}"},
        ).json()

        resp = client.put(
            f"/api/v1/cart/items/{created['id']}",
            json={"quantity": 5},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp.status_code == 404

    def test_update_quantity_exceeding_stock_returns_400(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 3})

        created = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        resp = client.put(
            f"/api/v1/cart/items/{created['id']}",
            json={"quantity": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_update_nonexistent_item_returns_404(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        resp = client.put(
            "/api/v1/cart/items/99999",
            json={"quantity": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_update_quantity_to_zero(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        created = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        resp = client.put(
            f"/api/v1/cart/items/{created['id']}",
            json={"quantity": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 0


class TestRemoveItem:
    def test_remove_item(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        created = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        ).json()

        resp = client.delete(
            f"/api/v1/cart/items/{created['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        # Verify cart is empty
        cart = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"}).json()
        assert cart["items"] == []

    def test_remove_other_users_item_returns_404(self, client: TestClient, db: Session):
        token1 = _create_user_token(db, "remove1@test.com")
        token2 = _create_user_token(db, "remove2@test.com")
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        created = client.post(
            "/api/v1/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token1}"},
        ).json()

        resp = client.delete(
            f"/api/v1/cart/items/{created['id']}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp.status_code == 404

    def test_remove_nonexistent_item_returns_404(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        resp = client.delete(
            "/api/v1/cart/items/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestClearCart:
    def test_clear_cart(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        p1 = _create_product(db, cat_id, {"sku": "CLR-001"})
        p2 = _create_product(db, cat_id, {"sku": "CLR-002", "title": "Second Product"})

        client.post(
            "/api/v1/cart/items",
            json={"product_id": p1.id, "quantity": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/api/v1/cart/items",
            json={"product_id": p2.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify 2 items
        cart = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"}).json()
        assert len(cart["items"]) == 2

        # Clear cart
        resp = client.delete("/api/v1/cart", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

        # Verify empty
        cart = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"}).json()
        assert cart["items"] == []


class TestCartTotal:
    def test_total_is_sum_of_item_quantity_times_price(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        p1 = _create_product(db, cat_id, {"sku": "TOT-001", "price": 10.0})
        p2 = _create_product(db, cat_id, {"sku": "TOT-002", "price": 15.50, "title": "Second"})

        client.post(
            "/api/v1/cart/items",
            json={"product_id": p1.id, "quantity": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/api/v1/cart/items",
            json={"product_id": p2.id, "quantity": 2},
            headers={"Authorization": f"Bearer {token}"},
        )

        cart = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"}).json()
        expected_total = round(3 * 10.0 + 2 * 15.50, 2)
        assert cart["total"] == expected_total

    def test_total_is_zero_for_empty_cart(self, client: TestClient, db: Session):
        token = _create_user_token(db)
        cart = client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"}).json()
        assert cart["total"] == 0

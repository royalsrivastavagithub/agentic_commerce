from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.cart import CartItem, SavedItem
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.core.security import create_access_token

SAMPLE_PRODUCT = {
    "title": "Saved Item Test Product",
    "description": "A product for save-for-later testing",
    "price": 29.99,
    "discountPercentage": 10.0,
    "rating": 4.5,
    "stock": 50,
    "tags": ["test"],
    "brand": "TestBrand",
    "sku": "SAVED-TST-001",
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


def _create_user_token(db: Session, email: str = "saveduser@test.com") -> str:
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


def _create_category(db: Session) -> int:
    cat = Category(name="saved-category")
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


def _add_cart_item(client: TestClient, product_id: int, token: str, qty: int = 1) -> dict:
    resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": product_id, "quantity": qty},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"add_cart_item failed: {resp.text}"
    return resp.json()


class TestAuthz:
    def test_get_saved_without_auth_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/cart/saved")
        assert resp.status_code == 401

    def test_save_item_without_auth_returns_401(self, client: TestClient):
        resp = client.post("/api/v1/cart/saved", json={"cart_item_id": 1})
        assert resp.status_code == 401

    def test_move_to_cart_without_auth_returns_401(self, client: TestClient):
        resp = client.post("/api/v1/cart/saved/1/move-to-cart")
        assert resp.status_code == 401

    def test_remove_saved_without_auth_returns_401(self, client: TestClient):
        resp = client.delete("/api/v1/cart/saved/1")
        assert resp.status_code == 401


class TestSaveForLater:

    def test_save_cart_item_moves_to_saved(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        cart_item = _add_cart_item(client, product.id, token)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["product_id"] == product.id
        assert "saved_at" in data

        assert db.query(CartItem).filter(CartItem.id == cart_item["id"]).first() is None

    def test_list_saved_items(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        cart_item = _add_cart_item(client, product.id, token)

        client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.get(
            "/api/v1/cart/saved",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["product_id"] == product.id

    def test_list_saved_items_empty(self, client, db):
        token = _create_user_token(db)
        resp = client.get(
            "/api/v1/cart/saved",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_move_saved_to_cart_creates_new_item(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        cart_item = _add_cart_item(client, product.id, token)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        saved_id = resp.json()["id"]

        resp = client.post(
            f"/api/v1/cart/saved/{saved_id}/move-to-cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == product.id
        assert data["quantity"] == 1

        assert db.query(SavedItem).filter(SavedItem.id == saved_id).first() is None

    def test_move_saved_to_cart_increments_existing_item(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        ci1 = _add_cart_item(client, product.id, token, qty=2)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": ci1["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        saved_id = resp.json()["id"]

        ci2 = _add_cart_item(client, product.id, token, qty=1)

        resp = client.post(
            f"/api/v1/cart/saved/{saved_id}/move-to-cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 2

    def test_save_same_product_twice_no_duplicate(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        cart_item = _add_cart_item(client, product.id, token)

        resp1 = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 201

        cart_item2 = _add_cart_item(client, product.id, token)
        resp2 = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item2["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 201
        assert resp2.json()["id"] == resp1.json()["id"]

        saved_count = db.query(SavedItem).filter(
            SavedItem.user_id == db.query(User).filter(User.email == "saveduser@test.com").first().id
        ).count()
        assert saved_count == 1

    def test_remove_saved_item(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        cart_item = _add_cart_item(client, product.id, token)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        saved_id = resp.json()["id"]

        resp = client.delete(
            f"/api/v1/cart/saved/{saved_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        assert db.query(SavedItem).filter(SavedItem.id == saved_id).first() is None

    def test_save_nonexistent_cart_item_returns_404(self, client, db):
        token = _create_user_token(db)
        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": 99999},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_move_nonexistent_saved_item_returns_404(self, client, db):
        token = _create_user_token(db)
        resp = client.post(
            "/api/v1/cart/saved/99999/move-to-cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_remove_nonexistent_saved_item_returns_404(self, client, db):
        token = _create_user_token(db)
        resp = client.delete(
            "/api/v1/cart/saved/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_user_cannot_save_another_users_cart_item(self, client, db):
        token1 = _create_user_token(db, email="user1@test.com")
        token2 = _create_user_token(db, email="user2@test.com")
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)

        cart_item = _add_cart_item(client, product.id, token1)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp.status_code == 404

    def test_saved_items_isolated_between_users(self, client, db):
        token1 = _create_user_token(db, email="user1@test.com")
        token2 = _create_user_token(db, email="user2@test.com")
        cat_id = _create_category(db)
        p1 = _create_product(db, cat_id, {"sku": "SAVED-ISO-001"})
        p2 = _create_product(db, cat_id, {"sku": "SAVED-ISO-002"})

        ci1 = _add_cart_item(client, p1.id, token1)
        ci2 = _add_cart_item(client, p2.id, token2)

        client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": ci1["id"]},
            headers={"Authorization": f"Bearer {token1}"},
        )
        client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": ci2["id"]},
            headers={"Authorization": f"Bearer {token2}"},
        )

        resp1 = client.get("/api/v1/cart/saved", headers={"Authorization": f"Bearer {token1}"})
        resp2 = client.get("/api/v1/cart/saved", headers={"Authorization": f"Bearer {token2}"})
        assert len(resp1.json()) == 1
        assert len(resp2.json()) == 1
        assert resp1.json()[0]["product_id"] == p1.id
        assert resp2.json()[0]["product_id"] == p2.id

    def test_move_to_cart_out_of_stock_returns_400(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id, {"stock": 5, "sku": "SAVED-OOS-001"})
        cart_item = _add_cart_item(client, product.id, token, qty=1)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        saved_id = resp.json()["id"]

        product.stock = 0
        db.commit()

        resp = client.post(
            f"/api/v1/cart/saved/{saved_id}/move-to-cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_saved_item_not_affected_by_clear_cart(self, client, db):
        token = _create_user_token(db)
        cat_id = _create_category(db)
        product = _create_product(db, cat_id)
        cart_item = _add_cart_item(client, product.id, token)

        resp = client.post(
            "/api/v1/cart/saved",
            json={"cart_item_id": cart_item["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        saved_id = resp.json()["id"]

        client.delete("/api/v1/cart", headers={"Authorization": f"Bearer {token}"})

        assert db.query(SavedItem).filter(SavedItem.id == saved_id).first() is not None

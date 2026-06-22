from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.core.security import create_access_token


_wl_counter = 0

def _setup(client: TestClient, db: Session, email: str = "wl@test.com", cat_name: str = "wl-cat"):
    global _wl_counter
    _wl_counter += 1
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

    cat = Category(name=cat_name)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    product = Product(
        title="Wishlist Product",
        description="test",
        category_id=cat.id,
        price=19.99,
        discount_percentage=0,
        rating=4,
        stock=10,
        tags=[],
        sku=f"WL-{_wl_counter:03d}",
        weight=1,
        dimensions={"width": 1, "height": 1, "depth": 1},
        warranty_information="1y",
        shipping_information="fast",
        availability_status="In Stock",
        reviews=[],
        return_policy="30d",
        minimum_order_quantity=1,
        meta={"createdAt": "", "updatedAt": "", "barcode": "", "qrCode": ""},
        images=[],
        thumbnail="https://example.com/thumb.jpg",
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return user, headers, product


class TestAuthz:
    def test_list_without_auth_returns_401(self, client: TestClient):
        assert client.get("/api/v1/wishlist").status_code == 401

    def test_add_without_auth_returns_401(self, client: TestClient):
        assert client.post("/api/v1/wishlist", json={"product_id": 1}).status_code == 401

    def test_remove_without_auth_returns_401(self, client: TestClient):
        assert client.delete("/api/v1/wishlist/1").status_code == 401


class TestWishlist:
    def test_empty_wishlist(self, client: TestClient, db: Session):
        _, headers, _ = _setup(client, db)
        resp = client.get("/api/v1/wishlist", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_to_wishlist(self, client: TestClient, db: Session):
        _, headers, product = _setup(client, db)
        resp = client.post("/api/v1/wishlist", json={"product_id": product.id}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["product_id"] == product.id
        assert data["product"]["title"] == product.title
        assert data["product"]["price"] == product.price

    def test_duplicate_returns_409(self, client: TestClient, db: Session):
        _, headers, product = _setup(client, db)
        client.post("/api/v1/wishlist", json={"product_id": product.id}, headers=headers)
        resp = client.post("/api/v1/wishlist", json={"product_id": product.id}, headers=headers)
        assert resp.status_code == 409

    def test_add_nonexistent_product_returns_404(self, client: TestClient, db: Session):
        _, headers, _ = _setup(client, db)
        resp = client.post("/api/v1/wishlist", json={"product_id": 99999}, headers=headers)
        assert resp.status_code == 404

    def test_list_returns_items_with_product_details(self, client: TestClient, db: Session):
        _, headers, product = _setup(client, db)
        client.post("/api/v1/wishlist", json={"product_id": product.id}, headers=headers)
        resp = client.get("/api/v1/wishlist", headers=headers)
        assert len(resp.json()) == 1
        assert resp.json()[0]["product"]["title"] == product.title

    def test_remove_from_wishlist(self, client: TestClient, db: Session):
        _, headers, product = _setup(client, db)
        created = client.post("/api/v1/wishlist", json={"product_id": product.id}, headers=headers).json()
        resp = client.delete(f"/api/v1/wishlist/{created['id']}", headers=headers)
        assert resp.status_code == 204
        assert client.get("/api/v1/wishlist", headers=headers).json() == []

    def test_remove_other_users_item_returns_404(self, client: TestClient, db: Session):
        _, headers1, product = _setup(client, db, "wl1@test.com")
        _, headers2, _ = _setup(client, db, "wl2@test.com", "wl-cat-2")
        created = client.post("/api/v1/wishlist", json={"product_id": product.id}, headers=headers1).json()
        resp = client.delete(f"/api/v1/wishlist/{created['id']}", headers=headers2)
        assert resp.status_code == 404

    def test_remove_nonexistent_returns_404(self, client: TestClient, db: Session):
        _, headers, _ = _setup(client, db)
        assert client.delete("/api/v1/wishlist/99999", headers=headers).status_code == 404

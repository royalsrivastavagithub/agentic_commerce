import jwt
from datetime import timedelta, timezone, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.category import Category
from app.models.user import User
from app.core.security import create_access_token


SAMPLE_PRODUCT = {
    "title": "Test Product",
    "description": "A sample product for testing",
    "price": 29.99,
    "discountPercentage": 10.0,
    "rating": 4.5,
    "stock": 50,
    "tags": ["test", "electronics"],
    "brand": "TestBrand",
    "sku": "TST-001",
    "weight": 1.5,
    "dimensions": {"width": 10.0, "height": 5.0, "depth": 3.0},
    "warrantyInformation": "1 year warranty",
    "shippingInformation": "Ships in 3-5 days",
    "availabilityStatus": "In Stock",
    "reviews": [
        {
            "rating": 5,
            "comment": "Great product!",
            "date": "2024-01-01T00:00:00Z",
            "reviewerName": "John Doe",
            "reviewerEmail": "john@example.com",
        }
    ],
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


def _create_category(
    client: TestClient, name: str = "electronics", headers: dict | None = None,
) -> dict:
    h = headers or {}
    resp = client.post("/api/v1/admin/categories", json={"name": name}, headers=h)
    if resp.status_code == 409:
        cats = client.get("/api/v1/categories").json()
        for c in cats:
            if c["name"] == name:
                return c
        raise AssertionError(f"Category '{name}' conflict but not in list")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    return resp.json()


def _create_product(
    client: TestClient,
    overrides: dict | None = None,
    headers: dict | None = None,
) -> dict:
    data = {**SAMPLE_PRODUCT}
    if overrides:
        data.update(overrides)
    if "category_id" not in data:
        cat = _create_category(client, headers=headers)
        data["category_id"] = cat["id"]
    resp = client.post("/api/v1/admin/products", json=data, headers=headers or {})
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    return resp.json()


class TestAuthzProductCRUD:
    def test_create_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"]},
        )
        assert resp.status_code == 401

    def test_create_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"]},
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_update_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "Hacked"},
        )
        assert resp.status_code == 401

    def test_update_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "Hacked"},
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_delete_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/products/{created['id']}")
        assert resp.status_code == 401


class TestListProducts:
    def test_empty_list(self, client: TestClient):
        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        body = resp.json()
        assert body["products"] == []
        assert body["total"] == 0
        assert body["skip"] == 0
        assert body["limit"] == 10

    def test_pagination(self, client: TestClient, admin_token_headers):
        for i in range(5):
            _create_product(client, {"sku": f"TST-PAG-{i}"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products?skip=0&limit=3")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["products"]) == 3
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 3

    def test_returns_camel_case(self, client: TestClient, admin_token_headers):
        _create_product(client, headers=admin_token_headers)
        resp = client.get("/api/v1/products")
        body = resp.json()
        product = body["products"][0]
        assert "discountPercentage" in product
        assert "warrantyInformation" in product
        assert "shippingInformation" in product
        assert "availabilityStatus" in product
        assert "returnPolicy" in product
        assert "minimumOrderQuantity" in product
        assert "discount_percentage" not in product


class TestCreateProduct:
    def test_create_minimal(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"]}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["title"] == "Test Product"
        assert body["category_id"] == cat["id"]
        assert body["category"] == "electronics"
        assert body["sku"] == "TST-001"

    def test_create_with_specific_id(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "id": 100, "sku": "TST-SID", "category_id": cat["id"]}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["id"] == 100

    def test_create_without_optional_brand(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "brand"}
        data["sku"] = "TST-NOBRAND"
        data["category_id"] = cat["id"]
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["brand"] is None

    def test_duplicate_id_returns_409(self, client: TestClient, admin_token_headers):
        _create_product(client, {"sku": "TST-DUP1"}, headers=admin_token_headers)
        cat = _create_category(client, "new-cat", headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "id": 1, "sku": "TST-DUP2", "category_id": cat["id"]},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_missing_required_field(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "title"}
        data["category_id"] = cat["id"]
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_without_sku(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "sku"}
        data["category_id"] = cat["id"]
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_empty_body(self, client: TestClient, admin_token_headers):
        resp = client.post("/api/v1/admin/products", json={}, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_negative_price(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-NEG", "price": -5.0},
            headers=admin_token_headers,
        )
        assert resp.status_code == 201

    def test_duplicate_sku_returns_409(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "sku": "DUP-SKU", "category_id": cat["id"]},
            headers=admin_token_headers,
        )
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "id": 999, "sku": "DUP-SKU", "category_id": cat["id"]},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409


class TestGetProduct:
    def test_get_existing(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/products/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_non_existing(self, client: TestClient):
        resp = client.get("/api/v1/products/99999")
        assert resp.status_code == 404

    def test_get_returns_camel_case(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/products/{created['id']}")
        body = resp.json()
        assert "discountPercentage" in body
        assert "warrantyInformation" in body
        assert "returnPolicy" in body
        assert "minimumOrderQuantity" in body


class TestUpdateProduct:
    def test_partial_update(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        pid = created["id"]
        resp = client.put(
            f"/api/v1/admin/products/{pid}",
            json={"title": "Updated Title", "price": 99.99},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Updated Title"
        assert body["price"] == 99.99
        assert body["sku"] == SAMPLE_PRODUCT["sku"]

    def test_update_non_existing(self, client: TestClient, admin_token_headers):
        resp = client.put(
            "/api/v1/admin/products/99999",
            json={"title": "Nope"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 404

    def test_update_with_camel_case_field(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        pid = created["id"]
        resp = client.put(
            f"/api/v1/admin/products/{pid}",
            json={"discountPercentage": 25.0},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["discountPercentage"] == 25.0

    def test_update_full_replacement(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        pid = created["id"]
        cat = _create_category(client, "new-category", headers=admin_token_headers)
        new_data = {
            "title": "Fully Replaced",
            "description": "Brand new description",
            "category_id": cat["id"],
            "price": 9.99,
            "discountPercentage": 5.0,
            "rating": 3.0,
            "stock": 1,
            "tags": ["new"],
            "sku": "TST-FULLREPLACE",
            "weight": 2.0,
            "dimensions": {"width": 1, "height": 1, "depth": 1},
            "warrantyInformation": "w",
            "shippingInformation": "s",
            "availabilityStatus": "In Stock",
            "reviews": [],
            "returnPolicy": "r",
            "minimumOrderQuantity": 1,
            "meta": {"createdAt": "2024-01-01", "updatedAt": "2024-01-01", "barcode": "b", "qrCode": "q"},
            "images": [],
            "thumbnail": "t.jpg",
        }
        resp = client.put(f"/api/v1/admin/products/{pid}", json=new_data, headers=admin_token_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Fully Replaced"
        assert body["sku"] == "TST-FULLREPLACE"

    def test_update_sets_required_field_to_null(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"sku": None},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_update_duplicate_sku_returns_409(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        p1 = _create_product(client, {"sku": "UNIQUE-SKU", "category_id": cat["id"]}, headers=admin_token_headers)
        p2 = _create_product(client, {"sku": "OTHER-SKU", "category_id": cat["id"]}, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{p2['id']}",
            json={"sku": "UNIQUE-SKU"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_update_empty_body(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == SAMPLE_PRODUCT["title"]

    def test_full_integration_flow(self, client: TestClient, admin_token_headers):
        c1 = _create_product(client, {"sku": "TST-FLOW"}, headers=admin_token_headers)
        pid = c1["id"]
        assert pid == 1
        r1 = client.get(f"/api/v1/products/{pid}")
        assert r1.status_code == 200
        assert r1.json()["title"] == "Test Product"
        r2 = client.put(
            f"/api/v1/admin/products/{pid}",
            json={"title": "Flow Updated", "price": 15.0},
            headers=admin_token_headers,
        )
        assert r2.status_code == 200
        assert r2.json()["title"] == "Flow Updated"
        r3 = client.get(f"/api/v1/products/{pid}")
        assert r3.json()["title"] == "Flow Updated"
        assert r3.json()["price"] == 15.0
        r4 = client.delete(f"/api/v1/admin/products/{pid}", headers=admin_token_headers)
        assert r4.status_code == 204
        r5 = client.get(f"/api/v1/products/{pid}")
        assert r5.status_code == 404


class TestDeleteProduct:
    def test_delete_existing(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        pid = created["id"]
        resp = client.delete(f"/api/v1/admin/products/{pid}", headers=admin_token_headers)
        assert resp.status_code == 204
        get_resp = client.get(f"/api/v1/products/{pid}")
        assert get_resp.status_code == 404

    def test_delete_non_existing(self, client: TestClient, admin_token_headers):
        resp = client.delete("/api/v1/admin/products/99999", headers=admin_token_headers)
        assert resp.status_code == 404


class TestSearchProducts:
    def test_search_found(self, client: TestClient, admin_token_headers):
        _create_product(client, {"sku": "TST-SRCH1"}, headers=admin_token_headers)
        _create_product(
            client, {"title": "Another Test Widget", "sku": "TST-SRCH2"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Widget")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["products"][0]["title"] == "Another Test Widget"

    def test_search_not_found(self, client: TestClient):
        resp = client.get("/api/v1/products/search?q=zzzzzzzzz")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_search_case_insensitive(self, client: TestClient, admin_token_headers):
        _create_product(client, {"title": "SearchMe", "sku": "TST-CASE"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=searchme")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_empty_query(self, client: TestClient):
        resp = client.get("/api/v1/products/search?q=")
        assert resp.status_code == 422

    def test_search_special_chars(self, client: TestClient, admin_token_headers):
        _create_product(client, {"title": "100% Cotton T-Shirt", "sku": "TST-SPC"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=100%25+Cotton")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_pagination(self, client: TestClient, admin_token_headers):
        _create_product(client, {"title": "Alpha Product", "sku": "TST-SP1"}, headers=admin_token_headers)
        _create_product(client, {"title": "Beta Product", "sku": "TST-SP2"}, headers=admin_token_headers)
        _create_product(client, {"title": "Gamma Product", "sku": "TST-SP3"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=Product&limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["products"]) == 2
        assert resp.json()["total"] == 3


class TestValidation:
    def test_negative_skip(self, client: TestClient):
        resp = client.get("/api/v1/products?skip=-1")
        assert resp.status_code == 422

    def test_zero_limit(self, client: TestClient):
        resp = client.get("/api/v1/products?limit=0")
        assert resp.status_code == 422

    def test_negative_limit(self, client: TestClient):
        resp = client.get("/api/v1/products?limit=-5")
        assert resp.status_code == 422

    def test_skip_beyond_total(self, client: TestClient, admin_token_headers):
        _create_product(client, headers=admin_token_headers)
        resp = client.get("/api/v1/products?skip=100")
        assert resp.status_code == 200
        assert resp.json()["products"] == []


class TestCategories:
    def test_categories_empty(self, client: TestClient):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_categories_with_products(self, client: TestClient, admin_token_headers):
        _create_category(client, "electronics", headers=admin_token_headers)
        _create_category(client, "books", headers=admin_token_headers)
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "electronics" in names
        assert "books" in names

    def test_categories_unique(self, client: TestClient, admin_token_headers):
        _create_category(client, "electronics", headers=admin_token_headers)
        resp = client.get("/api/v1/categories")
        cats = resp.json()
        assert len(cats) == 1

    def test_products_by_category(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, "electronics", headers=admin_token_headers)
        _create_product(
            client, {"sku": "TST-BYCAT1"}, headers=admin_token_headers,
        )
        resp = client.get(f"/api/v1/categories/{cat['id']}/products")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_products_by_category_not_found(self, client: TestClient):
        resp = client.get("/api/v1/categories/999/products")
        assert resp.status_code == 404

    def test_products_by_category_pagination(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, "electronics", headers=admin_token_headers)
        _create_product(client, {"sku": "TST-CATP1"}, headers=admin_token_headers)
        _create_product(client, {"sku": "TST-CATP2"}, headers=admin_token_headers)
        _create_product(client, {"sku": "TST-CATP3"}, headers=admin_token_headers)
        resp = client.get(f"/api/v1/categories/{cat['id']}/products?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["products"]) == 2
        assert resp.json()["total"] == 3

    def test_products_by_category_skip_beyond(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, "electronics", headers=admin_token_headers)
        _create_product(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/categories/{cat['id']}/products?skip=100")
        assert resp.status_code == 200
        assert resp.json()["products"] == []


class TestProductInDB:
    def test_product_persisted(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        db_product = db.query(Product).filter(Product.id == created["id"]).first()
        assert db_product is not None
        assert db_product.title == "Test Product"
        assert db_product.sku == "TST-001"

    def test_product_deleted_from_db(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        pid = created["id"]
        client.delete(f"/api/v1/admin/products/{pid}", headers=admin_token_headers)
        db_product = db.query(Product).filter(Product.id == pid).first()
        assert db_product is None


class TestAuthzExtended:
    def test_delete_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.delete(
            f"/api/v1/admin/products/{created['id']}",
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_expired_admin_token_on_create_returns_401(self, client: TestClient, db: Session, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        admin = User(
            email="exp-admin@test.com",
            hashed_password="x",
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        expired = create_access_token(
            subject=admin.id, role=admin.role, expires_delta=timedelta(seconds=-1)
        )
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"]},
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401

    def test_expired_admin_token_on_update_returns_401(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        admin = User(
            email="exp-admin2@test.com",
            hashed_password="x",
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        expired = create_access_token(
            subject=admin.id, role=admin.role, expires_delta=timedelta(seconds=-1)
        )
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "nope"},
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401

    def test_expired_admin_token_on_delete_returns_401(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        admin = User(
            email="exp-admin3@test.com",
            hashed_password="x",
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        expired = create_access_token(
            subject=admin.id, role=admin.role, expires_delta=timedelta(seconds=-1)
        )
        resp = client.delete(
            f"/api/v1/admin/products/{created['id']}",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401

    def test_malformed_token_on_delete_returns_401(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.delete(
            f"/api/v1/admin/products/{created['id']}",
            headers={"Authorization": "Bearer garbage.invalid.token"},
        )
        assert resp.status_code == 401

    def test_malformed_token_on_update_returns_401(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "nope"},
            headers={"Authorization": "Bearer garbage.invalid.token"},
        )
        assert resp.status_code == 401


class TestCreateProductEdgeCases:
    def test_create_with_empty_tags(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-EMPTYTAGS", "tags": []}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["tags"] == []

    def test_create_zero_price(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-ZEROPRICE", "price": 0.0}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["price"] == 0.0

    def test_create_zero_stock(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-ZEROSTOCK", "stock": 0}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["stock"] == 0

    def test_create_negative_stock(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-NEGSTOCK", "stock": -5}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201

    def test_create_max_integers(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {
            **SAMPLE_PRODUCT,
            "category_id": cat["id"],
            "sku": "TST-MAXINT",
            "price": 999999.99,
            "stock": 2**31 - 1,
            "rating": 5.0,
            "minimumOrderQuantity": 2**31 - 1,
        }
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["price"] == 999999.99
        assert body["stock"] == 2**31 - 1
        assert body["minimumOrderQuantity"] == 2**31 - 1

    def test_create_with_null_brand_explicitly(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-NULLBRAND", "brand": None}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["brand"] is None

    def test_update_wrong_data_type_for_price(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"price": "not-a-number"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 422

    def test_update_wrong_data_type_for_stock(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"stock": "not-an-integer"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 422

    def test_update_set_optional_field_to_null(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        assert created["brand"] == "TestBrand"
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"brand": None},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["brand"] is None

    def test_create_with_invalid_category_id_returns_400(self, client: TestClient, admin_token_headers):
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": 99999, "sku": "TST-BADCAT"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 400

    def test_update_with_invalid_category_id_returns_400(self, client: TestClient, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"category_id": 99999},
            headers=admin_token_headers,
        )
        assert resp.status_code == 400


class TestSearchEdgeCases:
    def test_search_sql_like_attempt(self, client: TestClient, admin_token_headers):
        _create_product(client, {"sku": "TST-SQLI"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=%27+OR+1%3D1--")
        assert resp.status_code == 200
        assert isinstance(resp.json()["products"], list)

    def test_search_unicode(self, client: TestClient, admin_token_headers):
        _create_product(
            client, {"title": "Café Français", "sku": "TST-UNI"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Caf%C3%A9")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_partial_substring(self, client: TestClient, admin_token_headers):
        _create_product(
            client, {"title": "Super Deluxe Widget Pro", "sku": "TST-PARTIAL"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Deluxe")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_with_numbers_only(self, client: TestClient, admin_token_headers):
        _create_product(
            client, {"title": "Model 2024 v3", "sku": "TST-NUM"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=2024")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_with_spaces(self, client: TestClient, admin_token_headers):
        _create_product(
            client, {"title": "Wireless Bluetooth Headphones", "sku": "TST-SPACE"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Wireless+Bluetooth")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestCategoryEdgeCases:
    def test_products_by_category_nonexistent_id(self, client: TestClient):
        resp = client.get("/api/v1/categories/99999/products")
        assert resp.status_code == 404

    def test_categories_after_all_products_deleted(self, client: TestClient, admin_token_headers):
        _create_category(client, "electronics", headers=admin_token_headers)
        cat = _create_category(client, "books", headers=admin_token_headers)
        _create_product(client, {"sku": "TST-CATDEL1"}, headers=admin_token_headers)
        _create_product(
            client, {"sku": "TST-CATDEL2", "category_id": cat["id"]},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/categories")
        assert len(resp.json()) == 2
        list_resp = client.get("/api/v1/products?limit=100")
        for p in list_resp.json()["products"]:
            client.delete(f"/api/v1/admin/products/{p['id']}", headers=admin_token_headers)
        resp2 = client.get("/api/v1/categories")
        assert len(resp2.json()) == 2  # categories persist independently

    def test_products_by_category_with_special_chars(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, "Men's & Women's", headers=admin_token_headers)
        _create_product(
            client, {"category_id": cat["id"], "sku": "TST-SPECAT"},
            headers=admin_token_headers,
        )
        resp = client.get(f"/api/v1/categories/{cat['id']}/products")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetProductEdgeCases:
    def test_get_product_negative_id(self, client: TestClient):
        resp = client.get("/api/v1/products/-1")
        assert resp.status_code == 404

    def test_get_product_zero_id(self, client: TestClient):
        resp = client.get("/api/v1/products/0")
        assert resp.status_code == 404

    def test_get_product_with_string_id(self, client: TestClient):
        resp = client.get("/api/v1/products/abc")
        assert resp.status_code == 422

    def test_get_product_very_large_id(self, client: TestClient):
        resp = client.get("/api/v1/products/999999999999")
        assert resp.status_code == 404


class TestProductModel:
    def test_product_created_with_all_fields_in_db(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        db_product = db.query(Product).filter(Product.id == created["id"]).first()
        assert db_product.title == SAMPLE_PRODUCT["title"]
        assert db_product.description == SAMPLE_PRODUCT["description"]
        assert db_product.price == SAMPLE_PRODUCT["price"]
        assert db_product.stock == SAMPLE_PRODUCT["stock"]
        assert db_product.sku == SAMPLE_PRODUCT["sku"]
        assert db_product.brand == SAMPLE_PRODUCT["brand"]
        assert db_product.rating == SAMPLE_PRODUCT["rating"]
        assert db_product.tags == SAMPLE_PRODUCT["tags"]

    def test_update_persists_to_db(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_product(client, headers=admin_token_headers)
        pid = created["id"]
        client.put(
            f"/api/v1/admin/products/{pid}",
            json={"title": "DB Updated", "price": 77.77},
            headers=admin_token_headers,
        )
        db_product = db.query(Product).filter(Product.id == pid).first()
        assert db_product.title == "DB Updated"
        assert db_product.price == 77.77


class TestAuthzCategoryCRUD:
    def test_create_without_auth_returns_401(self, client: TestClient):
        resp = client.post("/api/v1/admin/categories", json={"name": "test"})
        assert resp.status_code == 401

    def test_create_with_user_role_returns_403(self, client: TestClient, user_token_headers):
        resp = client.post(
            "/api/v1/admin/categories", json={"name": "test"}, headers=user_token_headers
        )
        assert resp.status_code == 403

    def test_update_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}", json={"name": "hacked"},
        )
        assert resp.status_code == 401

    def test_update_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={"name": "hacked"},
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_delete_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}")
        assert resp.status_code == 401

    def test_delete_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.delete(
            f"/api/v1/admin/categories/{cat['id']}", headers=user_token_headers,
        )
        assert resp.status_code == 403


class TestCreateCategory:
    def test_create_minimal(self, client: TestClient, admin_token_headers):
        resp = client.post(
            "/api/v1/admin/categories", json={"name": "electronics"}, headers=admin_token_headers
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "electronics"
        assert "id" in body

    def test_create_duplicate(self, client: TestClient, admin_token_headers):
        _create_category(client, "electronics", headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/categories", json={"name": "electronics"}, headers=admin_token_headers
        )
        assert resp.status_code == 409

    def test_create_empty_name(self, client: TestClient, admin_token_headers):
        resp = client.post(
            "/api/v1/admin/categories", json={"name": ""}, headers=admin_token_headers
        )
        assert resp.status_code == 201

    def test_create_empty_body(self, client: TestClient, admin_token_headers):
        resp = client.post("/api/v1/admin/categories", json={}, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_multiple(self, client: TestClient, admin_token_headers):
        _create_category(client, "a", headers=admin_token_headers)
        _create_category(client, "b", headers=admin_token_headers)
        _create_category(client, "c", headers=admin_token_headers)
        resp = client.get("/api/v1/categories")
        assert len(resp.json()) == 3


class TestGetCategory:
    def test_get_existing(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/categories/{cat['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "electronics"

    def test_get_non_existing(self, client: TestClient):
        resp = client.get("/api/v1/categories/99999")
        assert resp.status_code == 404

    def test_get_negative_id(self, client: TestClient):
        resp = client.get("/api/v1/categories/-1")
        assert resp.status_code == 404


class TestUpdateCategory:
    def test_update_name(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={"name": "new-name"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "new-name"

    def test_update_nonexistent(self, client: TestClient, admin_token_headers):
        resp = client.put(
            "/api/v1/admin/categories/99999",
            json={"name": "nope"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 404

    def test_update_duplicate_name(self, client: TestClient, admin_token_headers):
        _create_category(client, "existing", headers=admin_token_headers)
        cat = _create_category(client, "original", headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={"name": "existing"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_update_empty_body(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "electronics"


class TestDeleteCategory:
    def test_delete_existing(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}", headers=admin_token_headers)
        assert resp.status_code == 204
        get_resp = client.get(f"/api/v1/categories/{cat['id']}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent(self, client: TestClient, admin_token_headers):
        resp = client.delete("/api/v1/admin/categories/99999", headers=admin_token_headers)
        assert resp.status_code == 404

    def test_delete_with_products_returns_409(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        _create_product(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}", headers=admin_token_headers)
        assert resp.status_code == 409
        assert "product" in resp.text.lower()

    def test_delete_after_products_removed(self, client: TestClient, admin_token_headers):
        cat = _create_category(client, headers=admin_token_headers)
        prod = _create_product(client, headers=admin_token_headers)
        client.delete(f"/api/v1/admin/products/{prod['id']}", headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}", headers=admin_token_headers)
        assert resp.status_code == 204


class TestCategoryInDB:
    def test_category_persisted(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_category(client, headers=admin_token_headers)
        db_cat = db.query(Category).filter(Category.id == created["id"]).first()
        assert db_cat is not None
        assert db_cat.name == "electronics"

    def test_category_deleted_from_db(self, client: TestClient, db: Session, admin_token_headers):
        created = _create_category(client, headers=admin_token_headers)
        cid = created["id"]
        client.delete(f"/api/v1/admin/categories/{cid}", headers=admin_token_headers)
        db_cat = db.query(Category).filter(Category.id == cid).first()
        assert db_cat is None

import jwt
from datetime import timedelta, timezone, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User
from app.core.security import create_access_token

from tests.conftest import api_create_category, api_create_product, SAMPLE_PRODUCT


class TestPriceRange:
    def test_empty_db_returns_zero(self, client: TestClient):
        resp = client.get("/api/v1/products/price-range")
        assert resp.status_code == 200
        assert resp.json() == {"min_price": 0, "max_price": 0}

    def test_returns_min_and_max_price(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "PR-1", "price": 10.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PR-2", "price": 5.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PR-3", "price": 99.99}, headers=admin_token_headers)

        resp = client.get("/api/v1/products/price-range")
        assert resp.status_code == 200
        assert resp.json() == {"min_price": 5.0, "max_price": 99.99}


class TestSortProducts:
    def test_default_sort_by_id_asc(self, client: TestClient, admin_token_headers):
        p1 = api_create_product(client, {"sku": "SRT-1"}, headers=admin_token_headers)
        p2 = api_create_product(client, {"sku": "SRT-2"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products")
        ids = [p["id"] for p in resp.json()["products"]]
        assert ids == sorted(ids)

    def test_sort_price_asc(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "SRT-P1", "price": 100.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "SRT-P2", "price": 50.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "SRT-P3", "price": 200.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?sort_by=price&sort_order=asc")
        prices = [p["price"] for p in resp.json()["products"]]
        assert prices == sorted(prices)

    def test_sort_price_desc(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "SRT-P1", "price": 100.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "SRT-P2", "price": 50.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "SRT-P3", "price": 200.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?sort_by=price&sort_order=desc")
        prices = [p["price"] for p in resp.json()["products"]]
        assert prices == sorted(prices, reverse=True)

    def test_sort_rating_desc(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "SRT-R1", "rating": 3.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "SRT-R2", "rating": 5.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "SRT-R3", "rating": 1.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?sort_by=rating&sort_order=desc")
        ratings = [p["rating"] for p in resp.json()["products"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_invalid_sort_by_returns_422(self, client: TestClient):
        resp = client.get("/api/v1/products?sort_by=invalid")
        assert resp.status_code == 422


class TestPriceFilter:
    def test_min_price(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "PF-1", "price": 10.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PF-2", "price": 25.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PF-3", "price": 50.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?min_price=20")
        prices = [p["price"] for p in resp.json()["products"]]
        assert all(p >= 20 for p in prices)

    def test_max_price(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "PF-4", "price": 10.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PF-5", "price": 25.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PF-6", "price": 50.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?max_price=30")
        prices = [p["price"] for p in resp.json()["products"]]
        assert all(p <= 30 for p in prices)

    def test_min_and_max_price(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "PF-7", "price": 10.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PF-8", "price": 25.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "PF-9", "price": 50.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?min_price=15&max_price=40")
        prices = [p["price"] for p in resp.json()["products"]]
        assert all(15 <= p <= 40 for p in prices)

    def test_negative_min_price_returns_422(self, client: TestClient):
        resp = client.get("/api/v1/products?min_price=-1")
        assert resp.status_code == 422


class TestMinRating:
    def test_filters_by_min_rating(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "MR-1", "rating": 5.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "MR-2", "rating": 3.0}, headers=admin_token_headers)
        api_create_product(client, {"sku": "MR-3", "rating": 4.0}, headers=admin_token_headers)

        resp = client.get("/api/v1/products?min_rating=4")
        ratings = [p["rating"] for p in resp.json()["products"]]
        assert all(r >= 4 for r in ratings)
        assert len(ratings) == 2

    def test_rating_above_5_returns_422(self, client: TestClient):
        resp = client.get("/api/v1/products?min_rating=6")
        assert resp.status_code == 422

class TestAuthzProductCRUD:
    def test_create_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"]},
        )
        assert resp.status_code == 401

    def test_create_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"]},
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_update_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "Hacked"},
        )
        assert resp.status_code == 401

    def test_update_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "Hacked"},
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_delete_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
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
            api_create_product(client, {"sku": f"TST-PAG-{i}"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products?skip=0&limit=3")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["products"]) == 3
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 3

    def test_returns_camel_case(self, client: TestClient, admin_token_headers):
        api_create_product(client, headers=admin_token_headers)
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
        cat = api_create_category(client, headers=admin_token_headers)
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
        cat = api_create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "id": 100, "sku": "TST-SID", "category_id": cat["id"]}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["id"] == 100

    def test_create_without_optional_brand(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "brand"}
        data["sku"] = "TST-NOBRAND"
        data["category_id"] = cat["id"]
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["brand"] is None

    def test_duplicate_id_returns_409(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "TST-DUP1"}, headers=admin_token_headers)
        cat = api_create_category(client, "new-cat", headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "id": 1, "sku": "TST-DUP2", "category_id": cat["id"]},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_missing_required_field(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "title"}
        data["category_id"] = cat["id"]
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_without_sku(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "sku"}
        data["category_id"] = cat["id"]
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_empty_body(self, client: TestClient, admin_token_headers):
        resp = client.post("/api/v1/admin/products", json={}, headers=admin_token_headers)
        assert resp.status_code == 422

    def test_create_negative_price(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.post(
            "/api/v1/admin/products",
            json={**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-NEG", "price": -5.0},
            headers=admin_token_headers,
        )
        assert resp.status_code == 201

    def test_duplicate_sku_returns_409(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/products/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_non_existing(self, client: TestClient):
        resp = client.get("/api/v1/products/99999")
        assert resp.status_code == 404

    def test_get_returns_camel_case(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/products/{created['id']}")
        body = resp.json()
        assert "discountPercentage" in body
        assert "warrantyInformation" in body
        assert "returnPolicy" in body
        assert "minimumOrderQuantity" in body


class TestUpdateProduct:
    def test_partial_update(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
        pid = created["id"]
        resp = client.put(
            f"/api/v1/admin/products/{pid}",
            json={"discountPercentage": 25.0},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["discountPercentage"] == 25.0

    def test_update_full_replacement(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        pid = created["id"]
        cat = api_create_category(client, "new-category", headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"sku": None},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_update_duplicate_sku_returns_409(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        p1 = api_create_product(client, {"sku": "UNIQUE-SKU", "category_id": cat["id"]}, headers=admin_token_headers)
        p2 = api_create_product(client, {"sku": "OTHER-SKU", "category_id": cat["id"]}, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{p2['id']}",
            json={"sku": "UNIQUE-SKU"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_update_empty_body(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == SAMPLE_PRODUCT["title"]

    def test_full_integration_flow(self, client: TestClient, admin_token_headers):
        c1 = api_create_product(client, {"sku": "TST-FLOW"}, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
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
        api_create_product(client, {"sku": "TST-SRCH1"}, headers=admin_token_headers)
        api_create_product(
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
        api_create_product(client, {"title": "SearchMe", "sku": "TST-CASE"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=searchme")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_empty_query(self, client: TestClient):
        resp = client.get("/api/v1/products/search?q=")
        assert resp.status_code == 422

    def test_search_special_chars(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "100% Cotton T-Shirt", "sku": "TST-SPC"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=100%25+Cotton")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_pagination(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "Alpha Product", "sku": "TST-SP1"}, headers=admin_token_headers)
        api_create_product(client, {"title": "Beta Product", "sku": "TST-SP2"}, headers=admin_token_headers)
        api_create_product(client, {"title": "Gamma Product", "sku": "TST-SP3"}, headers=admin_token_headers)
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
        api_create_product(client, headers=admin_token_headers)
        resp = client.get("/api/v1/products?skip=100")
        assert resp.status_code == 200
        assert resp.json()["products"] == []



class TestProductInDB:
    def test_product_persisted(self, client: TestClient, db: Session, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        db_product = db.query(Product).filter(Product.id == created["id"]).first()
        assert db_product is not None
        assert db_product.title == "Test Product"
        assert db_product.sku == "TST-001"

    def test_product_deleted_from_db(self, client: TestClient, db: Session, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        pid = created["id"]
        client.delete(f"/api/v1/admin/products/{pid}", headers=admin_token_headers)
        db_product = db.query(Product).filter(Product.id == pid).first()
        assert db_product is None


class TestAuthzExtended:
    def test_delete_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.delete(
            f"/api/v1/admin/products/{created['id']}",
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_expired_admin_token_on_create_returns_401(self, client: TestClient, db: Session, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.delete(
            f"/api/v1/admin/products/{created['id']}",
            headers={"Authorization": "Bearer garbage.invalid.token"},
        )
        assert resp.status_code == 401

    def test_malformed_token_on_update_returns_401(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"title": "nope"},
            headers={"Authorization": "Bearer garbage.invalid.token"},
        )
        assert resp.status_code == 401


class TestCreateProductEdgeCases:
    def test_create_with_empty_tags(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-EMPTYTAGS", "tags": []}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["tags"] == []

    def test_create_zero_price(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-ZEROPRICE", "price": 0.0}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["price"] == 0.0

    def test_create_zero_stock(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-ZEROSTOCK", "stock": 0}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["stock"] == 0

    def test_create_negative_stock(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-NEGSTOCK", "stock": -5}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201

    def test_create_max_integers(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
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
        cat = api_create_category(client, headers=admin_token_headers)
        data = {**SAMPLE_PRODUCT, "category_id": cat["id"], "sku": "TST-NULLBRAND", "brand": None}
        resp = client.post("/api/v1/admin/products", json=data, headers=admin_token_headers)
        assert resp.status_code == 201
        assert resp.json()["brand"] is None

    def test_update_wrong_data_type_for_price(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"price": "not-a-number"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 422

    def test_update_wrong_data_type_for_stock(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"stock": "not-an-integer"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 422

    def test_update_set_optional_field_to_null(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/products/{created['id']}",
            json={"category_id": 99999},
            headers=admin_token_headers,
        )
        assert resp.status_code == 400


class TestSearchEdgeCases:
    def test_search_sql_like_attempt(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "TST-SQLI"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=%27+OR+1%3D1--")
        assert resp.status_code == 200
        assert isinstance(resp.json()["products"], list)

    def test_search_unicode(self, client: TestClient, admin_token_headers):
        api_create_product(
            client, {"title": "Café Français", "sku": "TST-UNI"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Caf%C3%A9")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_partial_substring(self, client: TestClient, admin_token_headers):
        api_create_product(
            client, {"title": "Super Deluxe Widget Pro", "sku": "TST-PARTIAL"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Deluxe")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_with_numbers_only(self, client: TestClient, admin_token_headers):
        api_create_product(
            client, {"title": "Model 2024 v3", "sku": "TST-NUM"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=2024")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_with_spaces(self, client: TestClient, admin_token_headers):
        api_create_product(
            client, {"title": "Wireless Bluetooth Headphones", "sku": "TST-SPACE"},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/products/search?q=Wireless+Bluetooth")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestFuzzySearch:
    def test_search_typo_still_finds_product(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "iPhone 15 Pro Max", "sku": "FZY-001"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=iphon")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "iPhone" in data["products"][0]["title"]

    def test_search_typo_multiple_words(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "Wireless Bluetooth Headphones", "sku": "FZY-002"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=wireles+blutooth")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_search_typo_short_word(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "Smartphone Pro", "sku": "FZY-003"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=smarphone")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_search_brand_match(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "Running Shoes", "brand": "Nike", "sku": "FZY-004"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=nkie")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_exact_ranks_higher_than_fuzzy(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"title": "Samsung Galaxy S24", "sku": "FZY-005"}, headers=admin_token_headers)
        api_create_product(client, {"title": "Phone Case for Samsung", "sku": "FZY-006"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=Samsung")
        data = resp.json()
        assert data["total"] >= 2
        assert data["products"][0]["title"] == "Samsung Galaxy S24"

    def test_search_no_match_returns_empty(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "FZY-007"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=zzzzzzzzzzzzzzz")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_search_response_has_thumbnail_price_title(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "FZY-008"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=Test")
        data = resp.json()
        p = data["products"][0]
        assert "thumbnail" in p
        assert "price" in p
        assert "title" in p

    def test_search_pagination_with_fuzzy(self, client: TestClient, admin_token_headers):
        for i in range(5):
            api_create_product(client, {"title": f"Product Alpha {i}", "sku": f"FZY-PAG-{i}"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/search?q=Alpha&skip=0&limit=2")
        data = resp.json()
        assert len(data["products"]) == 2
        assert data["total"] == 5



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


class TestFeaturedProducts:
    def test_empty_featured(self, client: TestClient):
        resp = client.get("/api/v1/products/featured")
        assert resp.status_code == 200
        body = resp.json()
        assert body["products"] == []
        assert body["total"] == 0

    def test_returns_featured_only(self, client: TestClient, admin_token_headers):
        p1 = api_create_product(client, {"sku": "FT-001", "is_featured": True}, headers=admin_token_headers)
        api_create_product(client, {"sku": "FT-002", "is_featured": False}, headers=admin_token_headers)
        api_create_product(client, {"sku": "FT-003"}, headers=admin_token_headers)

        resp = client.get("/api/v1/products/featured")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["products"][0]["id"] == p1["id"]
        assert body["products"][0]["is_featured"] is True

    def test_pagination(self, client: TestClient, admin_token_headers):
        for i in range(5):
            api_create_product(client, {"sku": f"FT-PAG-{i}", "is_featured": True}, headers=admin_token_headers)

        resp = client.get("/api/v1/products/featured?skip=0&limit=3")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["products"]) == 3
        assert body["total"] == 5

        resp2 = client.get("/api/v1/products/featured?skip=3&limit=3")
        assert len(resp2.json()["products"]) == 2

    def test_defaults_to_false(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "FT-DEF"}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/featured")
        assert resp.json()["total"] == 0

    def test_update_sets_is_featured(self, client: TestClient, admin_token_headers):
        created = api_create_product(client, {"sku": "FT-UPD"}, headers=admin_token_headers)
        pid = created["id"]

        resp = client.get("/api/v1/products/featured")
        assert resp.json()["total"] == 0

        client.put(
            f"/api/v1/admin/products/{pid}",
            json={"is_featured": True},
            headers=admin_token_headers,
        )

        resp = client.get("/api/v1/products/featured")
        assert resp.json()["total"] == 1
        assert resp.json()["products"][0]["id"] == pid

    def test_returns_camel_case(self, client: TestClient, admin_token_headers):
        api_create_product(client, {"sku": "FT-CAMEL", "is_featured": True}, headers=admin_token_headers)
        resp = client.get("/api/v1/products/featured")
        product = resp.json()["products"][0]
        assert "discountPercentage" in product
        assert "warrantyInformation" in product
        assert "is_featured" in product


class TestProductModel:
    def test_product_created_with_all_fields_in_db(self, client: TestClient, db: Session, admin_token_headers):
        created = api_create_product(client, headers=admin_token_headers)
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
        created = api_create_product(client, headers=admin_token_headers)
        pid = created["id"]
        client.put(
            f"/api/v1/admin/products/{pid}",
            json={"title": "DB Updated", "price": 77.77},
            headers=admin_token_headers,
        )
        db_product = db.query(Product).filter(Product.id == pid).first()
        assert db_product.title == "DB Updated"
        assert db_product.price == 77.77




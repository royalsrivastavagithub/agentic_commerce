from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.category import Category
from tests.conftest import api_create_category, api_create_product


class TestCategories:
    def test_categories_empty(self, client: TestClient):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_categories_with_products(self, client: TestClient, admin_token_headers):
        api_create_category(client, "electronics", headers=admin_token_headers)
        api_create_category(client, "books", headers=admin_token_headers)
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "electronics" in names
        assert "books" in names

    def test_categories_unique(self, client: TestClient, admin_token_headers):
        api_create_category(client, "electronics", headers=admin_token_headers)
        resp = client.get("/api/v1/categories")
        cats = resp.json()
        assert len(cats) == 1

    def test_products_by_category(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, "electronics", headers=admin_token_headers)
        api_create_product(
            client, {"sku": "TST-BYCAT1"}, headers=admin_token_headers,
        )
        resp = client.get(f"/api/v1/categories/{cat['id']}/products")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_products_by_category_not_found(self, client: TestClient):
        resp = client.get("/api/v1/categories/999/products")
        assert resp.status_code == 404

    def test_products_by_category_pagination(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, "electronics", headers=admin_token_headers)
        api_create_product(client, {"sku": "TST-CATP1"}, headers=admin_token_headers)
        api_create_product(client, {"sku": "TST-CATP2"}, headers=admin_token_headers)
        api_create_product(client, {"sku": "TST-CATP3"}, headers=admin_token_headers)
        resp = client.get(f"/api/v1/categories/{cat['id']}/products?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["products"]) == 2
        assert resp.json()["total"] == 3

    def test_products_by_category_skip_beyond(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, "electronics", headers=admin_token_headers)
        api_create_product(client, headers=admin_token_headers)
        resp = client.get(f"/api/v1/categories/{cat['id']}/products?skip=100")
        assert resp.status_code == 200
        assert resp.json()["products"] == []


class TestCategoryEdgeCases:
    def test_products_by_category_nonexistent_id(self, client: TestClient):
        resp = client.get("/api/v1/categories/99999/products")
        assert resp.status_code == 404

    def test_categories_after_all_products_deleted(self, client: TestClient, admin_token_headers):
        api_create_category(client, "electronics", headers=admin_token_headers)
        cat = api_create_category(client, "books", headers=admin_token_headers)
        api_create_product(client, {"sku": "TST-CATDEL1"}, headers=admin_token_headers)
        api_create_product(
            client, {"sku": "TST-CATDEL2", "category_id": cat["id"]},
            headers=admin_token_headers,
        )
        resp = client.get("/api/v1/categories")
        assert len(resp.json()) == 2
        list_resp = client.get("/api/v1/products?limit=100")
        for p in list_resp.json()["products"]:
            client.delete(f"/api/v1/admin/products/{p['id']}", headers=admin_token_headers)
        resp2 = client.get("/api/v1/categories")
        assert len(resp2.json()) == 2

    def test_products_by_category_with_special_chars(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, "Men's & Women's", headers=admin_token_headers)
        api_create_product(
            client, {"category_id": cat["id"], "sku": "TST-SPECAT"},
            headers=admin_token_headers,
        )
        resp = client.get(f"/api/v1/categories/{cat['id']}/products")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


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
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}", json={"name": "hacked"},
        )
        assert resp.status_code == 401

    def test_update_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={"name": "hacked"},
            headers=user_token_headers,
        )
        assert resp.status_code == 403

    def test_delete_without_auth_returns_401(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}")
        assert resp.status_code == 401

    def test_delete_with_user_role_returns_403(self, client: TestClient, admin_token_headers, user_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
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
        api_create_category(client, "electronics", headers=admin_token_headers)
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
        api_create_category(client, "a", headers=admin_token_headers)
        api_create_category(client, "b", headers=admin_token_headers)
        api_create_category(client, "c", headers=admin_token_headers)
        resp = client.get("/api/v1/categories")
        assert len(resp.json()) == 3


class TestGetCategory:
    def test_get_existing(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
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
        cat = api_create_category(client, headers=admin_token_headers)
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
        api_create_category(client, "existing", headers=admin_token_headers)
        cat = api_create_category(client, "original", headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={"name": "existing"},
            headers=admin_token_headers,
        )
        assert resp.status_code == 409

    def test_update_empty_body(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.put(
            f"/api/v1/admin/categories/{cat['id']}",
            json={},
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "electronics"


class TestDeleteCategory:
    def test_delete_existing(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}", headers=admin_token_headers)
        assert resp.status_code == 204
        get_resp = client.get(f"/api/v1/categories/{cat['id']}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent(self, client: TestClient, admin_token_headers):
        resp = client.delete("/api/v1/admin/categories/99999", headers=admin_token_headers)
        assert resp.status_code == 404

    def test_delete_with_products_returns_409(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        api_create_product(client, headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}", headers=admin_token_headers)
        assert resp.status_code == 409
        assert "product" in resp.text.lower()

    def test_delete_after_products_removed(self, client: TestClient, admin_token_headers):
        cat = api_create_category(client, headers=admin_token_headers)
        prod = api_create_product(client, headers=admin_token_headers)
        client.delete(f"/api/v1/admin/products/{prod['id']}", headers=admin_token_headers)
        resp = client.delete(f"/api/v1/admin/categories/{cat['id']}", headers=admin_token_headers)
        assert resp.status_code == 204


class TestCategoryInDB:
    def test_category_persisted(self, client: TestClient, db: Session, admin_token_headers):
        created = api_create_category(client, headers=admin_token_headers)
        db_cat = db.query(Category).filter(Category.id == created["id"]).first()
        assert db_cat is not None
        assert db_cat.name == "electronics"

    def test_category_deleted_from_db(self, client: TestClient, db: Session, admin_token_headers):
        created = api_create_category(client, headers=admin_token_headers)
        cid = created["id"]
        client.delete(f"/api/v1/admin/categories/{cid}", headers=admin_token_headers)
        db_cat = db.query(Category).filter(Category.id == cid).first()
        assert db_cat is None

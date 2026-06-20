from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product


SAMPLE_PRODUCT = {
    "title": "Test Product",
    "description": "A sample product for testing",
    "category": "electronics",
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


def _create_product(client: TestClient, overrides: dict | None = None) -> dict:
    data = {**SAMPLE_PRODUCT}
    if overrides:
        data.update(overrides)
    resp = client.post("/api/v1/products", json=data)
    assert resp.status_code == 201
    return resp.json()


class TestListProducts:
    def test_empty_list(self, client: TestClient):
        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        body = resp.json()
        assert body["products"] == []
        assert body["total"] == 0
        assert body["skip"] == 0
        assert body["limit"] == 10

    def test_pagination(self, client: TestClient):
        for i in range(5):
            _create_product(client, {"sku": f"TST-PAG-{i}"})
        resp = client.get("/api/v1/products?skip=0&limit=3")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["products"]) == 3
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 3

    def test_returns_camel_case(self, client: TestClient):
        _create_product(client)
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
    def test_create_minimal(self, client: TestClient):
        resp = client.post("/api/v1/products", json=SAMPLE_PRODUCT)
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["title"] == "Test Product"
        assert body["category"] == "electronics"
        assert body["sku"] == "TST-001"

    def test_create_with_specific_id(self, client: TestClient):
        data = {**SAMPLE_PRODUCT, "id": 100, "sku": "TST-SID"}
        resp = client.post("/api/v1/products", json=data)
        assert resp.status_code == 201
        assert resp.json()["id"] == 100

    def test_create_without_optional_brand(self, client: TestClient):
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "brand"}
        data["sku"] = "TST-NOBRAND"
        resp = client.post("/api/v1/products", json=data)
        assert resp.status_code == 201
        assert resp.json()["brand"] is None

    def test_duplicate_id_returns_409(self, client: TestClient):
        _create_product(client, {"sku": "TST-DUP1"})
        resp = client.post(
            "/api/v1/products",
            json={**SAMPLE_PRODUCT, "id": 1, "sku": "TST-DUP2"},
        )
        assert resp.status_code == 409

    def test_missing_required_field(self, client: TestClient):
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "title"}
        resp = client.post("/api/v1/products", json=data)
        assert resp.status_code == 422

    def test_create_without_sku(self, client: TestClient):
        data = {k: v for k, v in SAMPLE_PRODUCT.items() if k != "sku"}
        resp = client.post("/api/v1/products", json=data)
        assert resp.status_code == 422

    def test_create_empty_body(self, client: TestClient):
        resp = client.post("/api/v1/products", json={})
        assert resp.status_code == 422

    def test_create_negative_price(self, client: TestClient):
        resp = client.post(
            "/api/v1/products",
            json={**SAMPLE_PRODUCT, "sku": "TST-NEG", "price": -5.0},
        )
        assert resp.status_code == 201


class TestGetProduct:
    def test_get_existing(self, client: TestClient):
        created = _create_product(client)
        resp = client.get(f"/api/v1/products/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_non_existing(self, client: TestClient):
        resp = client.get("/api/v1/products/99999")
        assert resp.status_code == 404

    def test_get_returns_camel_case(self, client: TestClient):
        created = _create_product(client)
        resp = client.get(f"/api/v1/products/{created['id']}")
        body = resp.json()
        assert "discountPercentage" in body
        assert "warrantyInformation" in body
        assert "returnPolicy" in body
        assert "minimumOrderQuantity" in body


class TestUpdateProduct:
    def test_partial_update(self, client: TestClient):
        created = _create_product(client)
        pid = created["id"]
        resp = client.put(
            f"/api/v1/products/{pid}",
            json={"title": "Updated Title", "price": 99.99},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Updated Title"
        assert body["price"] == 99.99
        assert body["sku"] == SAMPLE_PRODUCT["sku"]

    def test_update_non_existing(self, client: TestClient):
        resp = client.put(
            "/api/v1/products/99999",
            json={"title": "Nope"},
        )
        assert resp.status_code == 404

    def test_update_with_camel_case_field(self, client: TestClient):
        created = _create_product(client)
        pid = created["id"]
        resp = client.put(
            f"/api/v1/products/{pid}",
            json={"discountPercentage": 25.0},
        )
        assert resp.status_code == 200
        assert resp.json()["discountPercentage"] == 25.0

    def test_update_full_replacement(self, client: TestClient):
        created = _create_product(client)
        pid = created["id"]
        new_data = {
            "title": "Fully Replaced",
            "description": "Brand new description",
            "category": "new-category",
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
        resp = client.put(f"/api/v1/products/{pid}", json=new_data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Fully Replaced"
        assert body["sku"] == "TST-FULLREPLACE"

    def test_update_sets_required_field_to_null(self, client: TestClient):
        created = _create_product(client)
        resp = client.put(
            f"/api/v1/products/{created['id']}",
            json={"sku": None},
        )
        assert resp.status_code == 409

    def test_update_empty_body(self, client: TestClient):
        created = _create_product(client)
        resp = client.put(
            f"/api/v1/products/{created['id']}",
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == SAMPLE_PRODUCT["title"]

    def test_full_integration_flow(self, client: TestClient):
        # create
        c1 = _create_product(client, {"sku": "TST-FLOW"})
        pid = c1["id"]
        assert pid == 1
        # read
        r1 = client.get(f"/api/v1/products/{pid}")
        assert r1.status_code == 200
        assert r1.json()["title"] == "Test Product"
        # update
        r2 = client.put(
            f"/api/v1/products/{pid}",
            json={"title": "Flow Updated", "price": 15.0},
        )
        assert r2.status_code == 200
        assert r2.json()["title"] == "Flow Updated"
        # read again
        r3 = client.get(f"/api/v1/products/{pid}")
        assert r3.json()["title"] == "Flow Updated"
        assert r3.json()["price"] == 15.0
        # delete
        r4 = client.delete(f"/api/v1/products/{pid}")
        assert r4.status_code == 204
        # read after delete
        r5 = client.get(f"/api/v1/products/{pid}")
        assert r5.status_code == 404


class TestDeleteProduct:
    def test_delete_existing(self, client: TestClient):
        created = _create_product(client)
        pid = created["id"]
        resp = client.delete(f"/api/v1/products/{pid}")
        assert resp.status_code == 204
        get_resp = client.get(f"/api/v1/products/{pid}")
        assert get_resp.status_code == 404

    def test_delete_non_existing(self, client: TestClient):
        resp = client.delete("/api/v1/products/99999")
        assert resp.status_code == 404


class TestSearchProducts:
    def test_search_found(self, client: TestClient):
        _create_product(client, {"sku": "TST-SRCH1"})
        _create_product(
            client, {"title": "Another Test Widget", "sku": "TST-SRCH2"}
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

    def test_search_case_insensitive(self, client: TestClient):
        _create_product(client, {"title": "SearchMe", "sku": "TST-CASE"})
        resp = client.get("/api/v1/products/search?q=searchme")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_empty_query(self, client: TestClient):
        resp = client.get("/api/v1/products/search?q=")
        assert resp.status_code == 422

    def test_search_special_chars(self, client: TestClient):
        _create_product(client, {"title": "100% Cotton T-Shirt", "sku": "TST-SPC"})
        resp = client.get("/api/v1/products/search?q=100%25+Cotton")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_pagination(self, client: TestClient):
        _create_product(client, {"title": "Alpha Product", "sku": "TST-SP1"})
        _create_product(client, {"title": "Beta Product", "sku": "TST-SP2"})
        _create_product(client, {"title": "Gamma Product", "sku": "TST-SP3"})
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

    def test_skip_beyond_total(self, client: TestClient):
        _create_product(client)
        resp = client.get("/api/v1/products?skip=100")
        assert resp.status_code == 200
        assert resp.json()["products"] == []


class TestCategories:
    def test_categories_empty(self, client: TestClient):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_categories_with_products(self, client: TestClient):
        _create_product(client)
        _create_product(client, {"category": "books", "sku": "TST-CAT2"})
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        assert "electronics" in resp.json()
        assert "books" in resp.json()

    def test_categories_unique(self, client: TestClient):
        _create_product(client)
        _create_product(client, {"sku": "TST-CAT3"})
        _create_product(client, {"sku": "TST-CAT4"})
        resp = client.get("/api/v1/categories")
        cats = resp.json()
        assert len(cats) == 1

    def test_products_by_category(self, client: TestClient):
        _create_product(client, {"sku": "TST-BYCAT1"})
        _create_product(client, {"category": "books", "sku": "TST-BYCAT2"})
        resp = client.get("/api/v1/categories/electronics")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_products_by_category_not_found(self, client: TestClient):
        resp = client.get("/api/v1/categories/nonexistent")
        assert resp.status_code == 404

    def test_products_by_category_pagination(self, client: TestClient):
        _create_product(client, {"sku": "TST-CATP1"})
        _create_product(client, {"sku": "TST-CATP2"})
        _create_product(client, {"sku": "TST-CATP3"})
        resp = client.get("/api/v1/categories/electronics?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["products"]) == 2
        assert resp.json()["total"] == 3

    def test_products_by_category_skip_beyond(self, client: TestClient):
        _create_product(client)
        resp = client.get("/api/v1/categories/electronics?skip=100")
        assert resp.status_code == 200
        assert resp.json()["products"] == []


class TestProductInDB:
    def test_product_persisted(self, client: TestClient, db: Session):
        created = _create_product(client)
        db_product = db.query(Product).filter(Product.id == created["id"]).first()
        assert db_product is not None
        assert db_product.title == "Test Product"
        assert db_product.sku == "TST-001"

    def test_product_deleted_from_db(self, client: TestClient, db: Session):
        created = _create_product(client)
        pid = created["id"]
        client.delete(f"/api/v1/products/{pid}")
        db_product = db.query(Product).filter(Product.id == pid).first()
        assert db_product is None

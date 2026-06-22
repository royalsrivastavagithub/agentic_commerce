from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Healthcheck" in data["message"]


def test_unknown_route_returns_404(client: TestClient):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404


def test_unknown_route_deep(client: TestClient):
    response = client.get("/api/v1/products/1/nonexistent")
    assert response.status_code == 404


def test_method_not_allowed(client: TestClient):
    response = client.put("/api/v1/health")
    assert response.status_code == 405


def test_openapi_schema_available(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/products" in schema["paths"]

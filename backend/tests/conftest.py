import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token

# Disable Typesense in tests
settings.TYPESENSE_ENABLED = False
# Ensure SECRET_KEY is set for test token generation
settings.SECRET_KEY = "test-secret-key-for-testing-min-32-chars!"
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


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


def api_create_category(
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


def api_create_product(
    client: TestClient,
    overrides: dict | None = None,
    headers: dict | None = None,
) -> dict:
    data = {**SAMPLE_PRODUCT}
    if overrides:
        data.update(overrides)
    if "category_id" not in data:
        cat = api_create_category(client, headers=headers)
        data["category_id"] = cat["id"]
    resp = client.post("/api/v1/admin/products", json=data, headers=headers or {})
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    return resp.json()

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test is done
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_token_headers(db):
    """Create an admin user and return authorization headers."""
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_verified=True,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    token = create_access_token(subject=admin.id, role=admin.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_token_headers(db):
    """Create a regular user and return authorization headers."""
    user = User(
        email="user@test.com",
        hashed_password=get_password_hash("user123"),
        is_active=True,
        is_verified=True,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def low_rate_limit():
    from app.core.config import settings
    original = settings.RATE_LIMIT
    settings.RATE_LIMIT = 5
    yield
    settings.RATE_LIMIT = original

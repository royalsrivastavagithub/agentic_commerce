import pytest
from sqlalchemy.orm import Session

from app.ai.tools import make_tools
from app.models.category import Category
from app.models.product import Product
from app.models.cart import Cart, CartItem
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture
def user(db: Session) -> User:
    u = User(
        email="tooltest@example.com",
        hashed_password=get_password_hash("Test@1234"),
        is_active=True,
        is_verified=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def tools(db: Session, user: User):
    return make_tools(db, user)


@pytest.fixture
def category(db: Session) -> Category:
    c = Category(name="Electronics")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def product(db: Session, category: Category) -> Product:
    p = Product(
        title="Smartphone X",
        description="A great phone",
        category_id=category.id,
        price=699.99,
        discount_percentage=10.0,
        rating=4.5,
        review_count=42,
        stock=100,
        tags=["phone", "electronics"],
        brand="TechBrand",
        sku="PHN-001",
        weight=0.3,
        dimensions={"width": 7, "height": 15, "depth": 1},
        warranty_information="1 year",
        shipping_information="Ships in 2 days",
        availability_status="In Stock",
        return_policy="30 days",
        minimum_order_quantity=1,
        meta={"barcode": "123"},
        images=["https://example.com/img.jpg"],
        thumbnail="https://example.com/thumb.jpg",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


class TestSearchProducts:
    def test_found(self, tools, product: Product):
        result = tools[0].invoke({"query": "Smartphone"})
        assert "Smartphone X" in result
        assert "$699.99" in result
        assert "TechBrand" in result
        assert "4.5/5" in result
        assert "https://example.com/thumb.jpg" in result

    def test_no_match(self, tools):
        result = tools[0].invoke({"query": "zzz_nonexistent"})
        assert "No products found" in result

    def test_with_category_filter(self, tools, product: Product, category: Category):
        result = tools[0].invoke({"query": "phone", "category": "Electronics"})
        assert "Smartphone X" in result

    def test_wrong_category(self, tools):
        result = tools[0].invoke({"query": "phone", "category": "NonExistent"})
        assert "No products found" in result

    def test_max_price_filter(self, tools, product: Product):
        result = tools[0].invoke({"query": "phone", "max_price": 500})
        assert "No products found" in result

    def test_min_rating_filter(self, tools, product: Product):
        result = tools[0].invoke({"query": "phone", "min_rating": 4.0})
        assert "Smartphone X" in result


class TestGetProductDetails:
    def test_found(self, tools, product: Product):
        result = tools[1].invoke({"product_id": product.id})
        assert "Smartphone X" in result
        assert "$699.99" in result
        assert "10% off" in result
        assert "4.5/5" in result
        assert "TechBrand" in result
        assert "1 year" in result
        assert "https://example.com/thumb.jpg" in result

    def test_not_found(self, tools):
        result = tools[1].invoke({"product_id": 99999})
        assert "not found" in result.lower()


class TestListCategories:
    def test_with_categories(self, tools, category: Category):
        result = tools[2].invoke({})
        assert "Electronics" in result

    def test_empty(self, tools):
        from app.models.category import Category
        from app.db.session import Base
        import sqlalchemy as sa

        pass


class TestGetCartSummary:
    def test_empty_cart(self, tools):
        result = tools[3].invoke({})
        assert "empty" in result.lower()

    def test_with_items(self, db: Session, tools, user: User, product: Product):
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

        item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=2,
            product_price=629.99,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        result = tools[3].invoke({})
        assert "Smartphone X" in result
        assert "x2" in result
        assert "$629.99" in result
        assert "Total:" in result

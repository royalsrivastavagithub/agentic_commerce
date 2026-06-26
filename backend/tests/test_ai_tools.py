import pytest
from app.ai.tools import make_context_tools
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.cart import Cart, CartItem


@pytest.fixture
def user(db):
    u = User(email="cart@test.com", hashed_password="h", is_active=True, is_verified=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def product(db):
    cat = Category(name="electronics")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    p = Product(
        title="Smartphone X",
        description="A phone",
        price=699.99,
        discount_percentage=5,
        rating=4.5,
        stock=50,
        tags=[],
        brand="TechBrand",
        sku="TST-001",
        weight=0.3,
        dimensions={"width": 1, "height": 2, "depth": 3},
        warranty_information="1 year",
        shipping_information="Ships fast",
        availability_status="In Stock",
        return_policy="30 days",
        minimum_order_quantity=1,
        meta={},
        images=[],
        thumbnail="https://example.com/thumb.jpg",
        category_id=cat.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def tools(db, user):
    return make_context_tools(db, user)


def _by_name(tools, name):
    for t in tools:
        if t.name == name:
            return t
    raise KeyError(name)


class TestSearchProducts:
    def test_found(self, tools, product):
        fn = _by_name(tools, "search_products")
        result = fn.invoke({"query": "Smartphone"})
        assert isinstance(result, dict)
        assert "product_ids" in result
        assert product.id in result["product_ids"]
        assert "Found" in result["message"]

    def test_no_match(self, tools):
        fn = _by_name(tools, "search_products")
        result = fn.invoke({"query": "zzzznotfound"})
        assert isinstance(result, dict)
        assert result["product_ids"] == []
        assert "No products found" in result["message"]

    def test_with_category_filter(self, tools, product, db):
        fn = _by_name(tools, "search_products")
        cat = db.query(Category).first()
        result = fn.invoke({"query": "Smartphone", "category": cat.name})
        assert isinstance(result, dict)
        assert product.id in result["product_ids"]

    def test_wrong_category(self, tools):
        fn = _by_name(tools, "search_products")
        result = fn.invoke({"query": "phone", "category": "nonexistent"})
        assert isinstance(result, dict)
        assert result["product_ids"] == []

    def test_max_price_filter(self, tools, product):
        fn = _by_name(tools, "search_products")
        result = fn.invoke({"query": "Smartphone", "max_price": 1000})
        assert isinstance(result, dict)
        assert product.id in result["product_ids"]

    def test_min_rating_param(self, tools, product):
        fn = _by_name(tools, "search_products")
        result = fn.invoke({"query": "Smartphone", "min_rating": 4.0})
        assert isinstance(result, dict)
        assert product.id in result["product_ids"]

    def test_min_price_param(self, tools, product):
        fn = _by_name(tools, "search_products")
        result = fn.invoke({"query": "Smartphone", "min_price": 500})
        assert isinstance(result, dict)
        assert product.id in result["product_ids"]


class TestHighestRated:
    def test_found(self, tools, product):
        fn = _by_name(tools, "highest_rated")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestLowestRated:
    def test_found(self, tools, product):
        fn = _by_name(tools, "lowest_rated")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestMostExpensive:
    def test_found(self, tools, product):
        fn = _by_name(tools, "most_expensive")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestCheapest:
    def test_found(self, tools, product):
        fn = _by_name(tools, "cheapest")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestBestDiscount:
    def test_found(self, tools, product):
        fn = _by_name(tools, "best_discount")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestMostReviewed:
    def test_found(self, tools, product):
        fn = _by_name(tools, "most_reviewed")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestLeastReviewed:
    def test_found(self, tools, product):
        fn = _by_name(tools, "least_reviewed")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestNewestArrivals:
    def test_found(self, tools, product):
        fn = _by_name(tools, "newest_arrivals")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestHighestStock:
    def test_found(self, tools, product):
        fn = _by_name(tools, "highest_stock")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestLowestStock:
    def test_found(self, tools, product):
        fn = _by_name(tools, "lowest_stock")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "product_ids" in result


class TestGetProductDetails:
    def test_found(self, tools, product):
        fn = _by_name(tools, "get_product_details")
        result = fn.invoke({"product_id": product.id})
        assert isinstance(result, dict)
        assert result["product_id"] == product.id
        assert result["title"] == product.title
        assert result["price"] == product.price

    def test_not_found(self, tools):
        fn = _by_name(tools, "get_product_details")
        result = fn.invoke({"product_id": 99999})
        assert isinstance(result, dict)
        assert "error" in result


class TestListCategories:
    def test_with_categories(self, tools, db):
        fn = _by_name(tools, "list_categories")
        cat = Category(name="books")
        db.add(cat)
        db.commit()
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert "categories" in result
        assert len(result["categories"]) > 0

    def test_empty(self, tools, db):
        fn = _by_name(tools, "list_categories")
        db.query(Category).delete()
        db.commit()
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert result["categories"] == []


class TestAddToCart:
    def test_add_product(self, tools, product):
        fn = _by_name(tools, "add_to_cart")
        result = fn.invoke({"product_name": product.title})
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["product_id"] == product.id

    def test_add_multiple(self, tools, product):
        fn = _by_name(tools, "add_to_cart")
        result = fn.invoke({"product_name": product.title, "quantity": 3})
        assert isinstance(result, dict)
        assert result["success"] is True

    def test_nonexistent_product(self, tools):
        fn = _by_name(tools, "add_to_cart")
        result = fn.invoke({"product_name": "Nonexistent Product"})
        assert isinstance(result, dict)
        assert result["success"] is False


class TestGetCartSummary:
    def test_empty_cart(self, tools):
        fn = _by_name(tools, "get_cart_summary")
        result = fn.invoke({})
        assert isinstance(result, dict)
        assert result["items"] == []
        assert result["total"] == 0.0

    def test_with_items(self, tools, user, product, db):
        fn = _by_name(tools, "get_cart_summary")
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=2,
            product_price=product.price,
        )
        db.add(item)
        db.commit()

        result = fn.invoke({})
        assert isinstance(result, dict)
        assert len(result["items"]) == 1
        assert result["total"] > 0
        assert product.id in result["product_ids"]


class TestUpdateCartItem:
    def test_update_quantity(self, tools, user, product, db):
        fn = _by_name(tools, "update_cart_item")
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        ci = CartItem(cart_id=cart.id, product_id=product.id, quantity=1, product_price=product.price)
        db.add(ci)
        db.commit()

        result = fn.invoke({"product_name": product.title, "quantity": 5})
        assert result["success"] is True

    def test_remove_by_zero(self, tools, user, product, db):
        fn = _by_name(tools, "update_cart_item")
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        ci = CartItem(cart_id=cart.id, product_id=product.id, quantity=1, product_price=product.price)
        db.add(ci)
        db.commit()

        result = fn.invoke({"product_name": product.title, "quantity": 0})
        assert result["success"] is True


class TestRemoveCartItem:
    def test_remove(self, tools, user, product, db):
        fn = _by_name(tools, "remove_cart_item")
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        ci = CartItem(cart_id=cart.id, product_id=product.id, quantity=1, product_price=product.price)
        db.add(ci)
        db.commit()

        result = fn.invoke({"product_name": product.title})
        assert result["success"] is True

    def test_not_in_cart(self, tools, user, db):
        fn = _by_name(tools, "remove_cart_item")
        result = fn.invoke({"product_name": "Nonexistent Product"})
        assert result["success"] is False


class TestClearCart:
    def test_clear(self, tools, user, product, db):
        fn = _by_name(tools, "clear_cart")
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        ci = CartItem(cart_id=cart.id, product_id=product.id, quantity=1, product_price=product.price)
        db.add(ci)
        db.commit()

        result = fn.invoke({})
        assert result["success"] is True

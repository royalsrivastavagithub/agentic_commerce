from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.core.exceptions import BadRequestError, NotFoundError
from app.services.cart_service import (
    add_cart_item as _add_cart_item,
    update_cart_item as _update_cart_item,
    remove_cart_item as _remove_cart_item,
    clear_cart as _clear_cart,
)
from app.services.product_service import search_products as _search_products
from app.services.product_service import get_product_by_id as _get_product_by_id


def _to_card(p: Product) -> dict:
    return {
        "product_id": p.id,
        "title": p.title,
        "price": p.price,
        "rating": p.rating,
        "brand": p.brand,
        "category": p.category,
        "thumbnail": p.thumbnail,
        "stock": p.stock,
        "description": p.description,
    }


def _make_context(db: Session, query: str | None, category: str | None) -> tuple[str | None, int | None]:
    search_query = query or ""
    category_id = None
    if category:
        cat = db.query(Category).filter(Category.name.ilike(category)).first()
        if cat:
            category_id = cat.id
        elif not search_query:
            search_query = category
    return search_query, category_id


def _tied_top(items: list[Product], attr: str, top_n: int = 10) -> tuple[list[Product], str]:
    """Filter sorted items to only those tied for the top value. Returns (filtered_items, label)."""
    if not items:
        return [], ""
    top_val = getattr(items[0], attr)
    tied = [p for p in items if getattr(p, attr) == top_val][:top_n]
    if len(tied) == 1:
        label = tied[0].title
    elif len(tied) <= 3:
        label = f"tie: {'; '.join(p.title for p in tied)}"
    else:
        label = f"{len(tied)} products tied at {top_val}"
    return tied, label



def _sort_guard(search_query: str, category: str | None) -> dict | None:
    if not search_query and not category:
        return {"message": "Please specify what to search for.", "product_ids": []}
    return None


def _fmt_tool_message(label: str, tied: list, attr_display: str) -> str:
    if len(tied) > 3:
        return label
    val = getattr(tied[0], attr_display)
    if attr_display == "price":
        return f"{label} (${val})"
    if attr_display == "discount_percentage":
        return f"{label} ({val}% off)"
    return f"{label} ({val})"


def make_context_tools(db: Session, user: User) -> list:

    # ── Search ──────────────────────────────────────────────

    @tool
    def search_products(
        query: str,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Search products by keyword with optional filters. Set in_stock=True for in-stock only, False for out-of-stock only. Returns matching product IDs."""
        search_query, category_id = _make_context(db, query, category)
        items, total = _search_products(
            db=db, q=search_query, category_id=category_id,
            min_price=min_price, max_price=max_price, min_rating=min_rating,
            in_stock=in_stock, limit=10,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        ids = [p.id for p in items]
        return {"message": f"Found {total} results.", "product_ids": ids}

    # ── Sort tools (tie-aware) ──────────────────────────────

    @tool
    def highest_rated(
        query: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the highest rated products by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-top product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            max_price=max_price, min_rating=min_rating, in_stock=in_stock,
            sort_by="rating", sort_order="desc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "rating")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Highest rated: {label}", tied, "rating")
        return {"message": msg, "product_ids": ids}

    @tool
    def lowest_rated(
        query: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the lowest rated products by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-bottom product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            max_price=max_price, in_stock=in_stock,
            sort_by="rating", sort_order="asc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "rating")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Lowest rated: {label}", tied, "rating")
        return {"message": msg, "product_ids": ids}

    @tool
    def most_expensive(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the most expensive products by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-top product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="price", sort_order="desc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "price")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Most expensive: {label}", tied, "price")
        return {"message": msg, "product_ids": ids}

    @tool
    def cheapest(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the cheapest products by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-bottom product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="price", sort_order="asc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "price")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Cheapest: {label}", tied, "price")
        return {"message": msg, "product_ids": ids}

    @tool
    def best_discount(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find products with the best discounts by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-top product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="discount", sort_order="desc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "discount_percentage")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Best discount: {label}", tied, "discount_percentage")
        return {"message": msg, "product_ids": ids}

    @tool
    def most_reviewed(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the most reviewed products by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-top product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="review_count", sort_order="desc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "review_count")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Most reviewed: {label}", tied, "review_count")
        return {"message": msg, "product_ids": ids}

    @tool
    def least_reviewed(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the least reviewed products by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-bottom product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="review_count", sort_order="asc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "review_count")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Least reviewed: {label}", tied, "review_count")
        return {"message": msg, "product_ids": ids}

    @tool
    def newest_arrivals(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find the newest product arrivals by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-top product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="created_at", sort_order="desc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "id")
        ids = [p.id for p in tied]
        return {"message": f"Newest: {label}", "product_ids": ids}

    @tool
    def highest_stock(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find products with the most stock by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-top product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="stock", sort_order="desc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "stock")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Highest stock: {label}", tied, "stock")
        return {"message": msg, "product_ids": ids}

    @tool
    def lowest_stock(
        query: str | None = None,
        category: str | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        """Find products with the lowest stock by optional keyword. Pass in_stock=True/False to filter by availability. Returns tied-for-bottom product IDs."""
        search_query, category_id = _make_context(db, query, category)
        guard = _sort_guard(search_query, category)
        if guard:
            return guard
        items, _ = _search_products(
            db=db, q=search_query, category_id=category_id,
            in_stock=in_stock,
            sort_by="stock", sort_order="asc", limit=20,
        )
        if not items:
            return {"message": "No products found.", "product_ids": []}
        tied, label = _tied_top(items, "stock")
        ids = [p.id for p in tied]
        msg = _fmt_tool_message(f"Lowest stock: {label}", tied, "stock")
        return {"message": msg, "product_ids": ids}

    # ── Product info ───────────────────────────────────────

    @tool
    def get_product_details(product_id: int) -> dict:
        """Get full details for a specific product by its ID. Returns the product object."""
        try:
            p = _get_product_by_id(db, product_id)
            return _to_card(p)
        except NotFoundError:
            return {"error": f"Product with ID {product_id} not found."}

    @tool
    def list_categories() -> dict:
        """List all available product categories."""
        cats = db.query(Category).order_by(Category.name).all()
        return {"categories": [c.name for c in cats]}

    # ── Cart operations ─────────────────────────────────────

    @tool
    def add_to_cart(product_name: str, quantity: int = 1) -> dict:
        """Add a product to your shopping cart by product name.

        Args:
            product_name: The exact product name to add (search first if unsure).
            quantity: How many units to add (default 1).
        """
        p = db.query(Product).filter(Product.title.ilike(product_name)).first()
        if not p:
            return {"success": False, "message": f"Could not find a product named '{product_name}'."}
        try:
            _add_cart_item(db, user.id, p.id, quantity)
            return {"success": True, "message": f"Added {quantity} × {p.title} to your cart.", "product_id": p.id}
        except (BadRequestError, NotFoundError) as e:
            return {"success": False, "message": str(e)}

    @tool
    def get_cart_summary() -> dict:
        """View the current user's shopping cart contents and total price."""
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart or not cart.items:
            return {"items": [], "total": 0.0, "message": "Your cart is empty."}

        items = []
        product_ids = []
        total = 0.0
        for item in cart.items:
            p = item.product
            if not p:
                continue
            product_ids.append(p.id)
            subtotal = item.quantity * item.product_price
            total += subtotal
            items.append({
                "product_id": p.id,
                "title": p.title,
                "quantity": item.quantity,
                "unit_price": item.product_price,
                "subtotal": round(subtotal, 2),
            })

        return {
            "items": items,
            "total": round(total, 2),
            "product_ids": product_ids,
            "message": f"Cart: {len(items)} item(s), ${total:.2f} total.",
        }

    @tool
    def update_cart_item(product_name: str, quantity: int) -> dict:
        """Update the quantity of a product in your cart by product name.

        Args:
            product_name: The product name whose cart quantity to change.
            quantity: New quantity (must be > 0). Set to 0 to remove.
        """
        p = db.query(Product).filter(Product.title.ilike(product_name)).first()
        if not p:
            return {"success": False, "message": f"Could not find a product named '{product_name}'."}
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return {"success": False, "message": "Cart is empty."}
        citem = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_id == p.id)
            .first()
        )
        if not citem:
            return {"success": False, "message": "Product not found in your cart."}
        try:
            if quantity <= 0:
                _remove_cart_item(db, user.id, citem.id)
                return {"success": True, "message": f"Removed product from cart.", "product_name": product_name}
            _update_cart_item(db, user.id, citem.id, quantity)
            return {"success": True, "message": f"Updated quantity to {quantity}.", "product_name": product_name}
        except (BadRequestError, NotFoundError) as e:
            return {"success": False, "message": str(e)}

    @tool
    def remove_cart_item(product_name: str) -> dict:
        """Remove a product from your shopping cart by product name.

        Args:
            product_name: The product name to remove from cart.
        """
        p = db.query(Product).filter(Product.title.ilike(product_name)).first()
        if not p:
            return {"success": False, "message": f"Could not find a product named '{product_name}'."}
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return {"success": False, "message": "Cart is empty."}
        citem = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_id == p.id)
            .first()
        )
        if not citem:
            return {"success": False, "message": "Product not found in your cart."}
        try:
            _remove_cart_item(db, user.id, citem.id)
            return {"success": True, "message": f"Removed from cart.", "product_name": product_name}
        except (BadRequestError, NotFoundError) as e:
            return {"success": False, "message": str(e)}

    @tool
    def clear_cart() -> dict:
        """Remove all items from your shopping cart."""
        _clear_cart(db, user.id)
        return {"success": True, "message": "Cart cleared."}

    return [
        search_products,
        highest_rated,
        lowest_rated,
        most_expensive,
        cheapest,
        best_discount,
        most_reviewed,
        least_reviewed,
        newest_arrivals,
        highest_stock,
        lowest_stock,
        get_product_details,
        list_categories,
        add_to_cart,
        get_cart_summary,
        update_cart_item,
        remove_cart_item,
        clear_cart,
    ]

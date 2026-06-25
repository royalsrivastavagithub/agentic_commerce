from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.core.exceptions import BadRequestError, NotFoundError
from app.services.cart_service import add_cart_item as _add_cart_item
from app.services.product_service import search_products as _search_products
from app.services.product_service import get_product_by_id as _get_product_by_id


def make_tools(db: Session, user: User, found_products: list | None = None) -> list:
    @tool
    def search_products(
        query: str,
        category: str | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        sort_by: str | None = None,
    ) -> str:
        """Search products by keyword with optional filters.

        Args:
            query: The search keyword to look for in product titles and brands.
            category: Optional category name to filter by (e.g. "Electronics").
            max_price: Optional maximum price filter.
            min_rating: Optional minimum rating filter (0-5).
            sort_by: Optional sort field ("price", "rating", "title").
        """
        category_id = None
        if category:
            cat = db.query(Category).filter(Category.name.ilike(category)).first()
            if cat:
                category_id = cat.id

        sort_order = "asc"
        if sort_by in ("price", "rating", "title"):
            field = sort_by
        else:
            field = ""
            sort_by = None

        items, total = _search_products(
            db=db,
            q=query,
            category_id=category_id,
            max_price=max_price,
            min_rating=min_rating,
            sort_by=field,
            sort_order=sort_order,
            limit=10,
        )

        if not items:
            return "No products found matching your criteria."

        lines = [f"Found {total} product(s):"]
        for p in items:
            if found_products is not None:
                found_products.append(p)
            price = f"${p.price:.2f}"
            rating = f"{p.rating}/5" if p.rating else "N/A"
            brand = f" [{p.brand}]" if p.brand else ""
            lines.append(f"- **{p.title}**{brand} (ID: {p.id}) — {price} ★{rating}")
        return "\n".join(lines)

    @tool
    def get_product_details(product_id: int) -> str:
        """Get full details for a specific product by its ID."""
        try:
            p = _get_product_by_id(db, product_id)
        except Exception:
            return f"Product with ID {product_id} not found."

        if found_products is not None:
            found_products.append(p)

        price = f"${p.price:.2f}"
        rating = f"{p.rating}/5" if p.rating else "N/A"
        stock = f"In stock ({p.stock} available)" if p.stock > 0 else "Out of stock"

        return (
            f"**{p.title}** (ID: {p.id}) — {price} ★{rating} — {p.brand or 'N/A'} — {p.category or 'N/A'}\n"
            f"{stock}\n"
            f"{p.description}"
        )

    @tool
    def list_categories() -> str:
        """List all available product categories."""
        cats = db.query(Category).order_by(Category.name).all()
        if not cats:
            return "No categories available."
        return "Available categories:\n" + "\n".join(f"- {c.name}" for c in cats)

    @tool
    def add_to_cart(product_id: int, quantity: int = 1) -> str:
        """Add a product to your shopping cart by product ID and quantity.

        Args:
            product_id: The ID of the product to add.
            quantity: How many units to add (default 1).
        """
        try:
            p = _get_product_by_id(db, product_id)
            _add_cart_item(db, user.id, product_id, quantity)
            return f"Added {quantity} × **{p.title}** (ID: {p.id}) to your cart."
        except (BadRequestError, NotFoundError) as e:
            return str(e)

    @tool
    def get_cart_summary() -> str:
        """View the current user's shopping cart contents and total price."""
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart or not cart.items:
            return "Your cart is empty."

        lines = ["Your cart:"]
        total = 0.0
        for item in cart.items:
            product = item.product
            if not product:
                continue
            subtotal = item.quantity * item.product_price
            total += subtotal
            lines.append(
                f"- {product.title} (ID: {product.id}) x{item.quantity} "
                f"@ ${item.product_price:.2f} = ${subtotal:.2f}"
            )
        lines.append(f"\nTotal: ${total:.2f}")
        return "\n".join(lines)

    return [search_products, get_product_details, list_categories, add_to_cart, get_cart_summary]

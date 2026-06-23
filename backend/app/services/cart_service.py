from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, BadRequestError
from app.models.cart import Cart, CartItem, SavedItem
from app.models.product import Product
from app.services.product_service import get_product_by_id


def compute_effective_price(product: Product) -> float:
    return round(product.price * (1 - product.discount_percentage / 100), 2)


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _compute_total(items: list[CartItem]) -> float:
    return round(sum(
        item.quantity * item.product_price for item in items if item.product
    ), 2)


def get_cart(db: Session, user_id: int) -> tuple[int, list[CartItem], float, datetime, datetime]:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        return 0, [], 0.0, datetime.now(), datetime.now()
    total = _compute_total(cart.items)
    return cart.id, cart.items, total, cart.created_at, cart.updated_at


def _get_cart_item(db: Session, item_id: int, user_id: int) -> CartItem:
    cart_item = (
        db.query(CartItem)
        .join(Cart)
        .filter(CartItem.id == item_id, Cart.user_id == user_id)
        .first()
    )
    if not cart_item:
        raise NotFoundError("Cart item not found")
    return cart_item


def add_cart_item(db: Session, user_id: int, product_id: int, quantity: int) -> CartItem:
    product = get_product_by_id(db, product_id)
    if quantity > product.stock:
        raise BadRequestError(f"Only {product.stock} units available")

    cart = get_or_create_cart(db, user_id)

    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )
    if existing:
        new_qty = existing.quantity + quantity
        if new_qty > product.stock:
            raise BadRequestError(
                f"Only {product.stock} units available (already have {existing.quantity})"
            )
        existing.quantity = new_qty
        db.commit()
        db.refresh(existing)
        return existing

    effective_price = compute_effective_price(product)
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=product_id,
        quantity=quantity,
        product_price=effective_price,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item(db: Session, user_id: int, item_id: int, quantity: int) -> CartItem:
    cart_item = _get_cart_item(db, item_id, user_id)
    if quantity > cart_item.product.stock:
        raise BadRequestError(f"Only {cart_item.product.stock} units available")
    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item


def remove_cart_item(db: Session, user_id: int, item_id: int) -> None:
    cart_item = _get_cart_item(db, item_id, user_id)
    db.delete(cart_item)
    db.commit()


def clear_cart(db: Session, user_id: int) -> None:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if cart:
        cart.items = []
        db.commit()


def list_saved_items(db: Session, user_id: int) -> list[SavedItem]:
    return (
        db.query(SavedItem)
        .filter(SavedItem.user_id == user_id)
        .order_by(SavedItem.saved_at.desc())
        .all()
    )


def save_cart_item(db: Session, user_id: int, cart_item_id: int) -> SavedItem:
    cart_item = _get_cart_item(db, cart_item_id, user_id)

    existing_saved = (
        db.query(SavedItem)
        .filter(SavedItem.user_id == user_id, SavedItem.product_id == cart_item.product_id)
        .first()
    )
    if existing_saved:
        db.delete(cart_item)
        db.commit()
        return existing_saved

    saved = SavedItem(user_id=user_id, product_id=cart_item.product_id)
    db.add(saved)
    db.delete(cart_item)
    db.commit()
    db.refresh(saved)
    return saved


def move_saved_to_cart(db: Session, user_id: int, saved_id: int) -> CartItem:
    saved = (
        db.query(SavedItem)
        .filter(SavedItem.id == saved_id, SavedItem.user_id == user_id)
        .first()
    )
    if not saved:
        raise NotFoundError("Saved item not found")

    product = db.query(Product).filter(Product.id == saved.product_id).first()
    if not product:
        raise NotFoundError("Product not found")

    cart = get_or_create_cart(db, user_id)

    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == saved.product_id)
        .first()
    )
    if existing:
        if existing.quantity + 1 > product.stock:
            raise BadRequestError(
                f"Only {product.stock} units available (already have {existing.quantity})"
            )
        existing.quantity += 1
        db.delete(saved)
        db.commit()
        db.refresh(existing)
        return existing

    if 1 > product.stock:
        raise BadRequestError("Product is out of stock")

    eff_price = compute_effective_price(product)
    cart_item = CartItem(cart_id=cart.id, product_id=saved.product_id, quantity=1, product_price=eff_price)
    db.add(cart_item)
    db.delete(saved)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def remove_saved_item(db: Session, user_id: int, saved_id: int) -> None:
    saved = (
        db.query(SavedItem)
        .filter(SavedItem.id == saved_id, SavedItem.user_id == user_id)
        .first()
    )
    if not saved:
        raise NotFoundError("Saved item not found")
    db.delete(saved)
    db.commit()

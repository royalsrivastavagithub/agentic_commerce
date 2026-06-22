from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cart import Cart, CartItem, SavedItem
from app.models.product import Product
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    SaveCartItemRequest,
    SavedItemResponse,
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cart", tags=["cart"])


def _get_or_create_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _compute_total(items: list[CartItem]) -> float:
    return round(sum(
        item.quantity * item.product.price for item in items if item.product
    ), 2)


@router.get("", response_model=CartResponse, summary="Get current user cart")
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        return CartResponse(
            id=0, items=[], total=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    total = _compute_total(cart.items)
    return CartResponse(
        id=cart.id, items=cart.items, total=total,
        created_at=cart.created_at, updated_at=cart.updated_at,
    )


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED, summary="Add item to cart (increments quantity if already present)")
def add_cart_item(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    if item_in.quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock} units available",
        )

    cart = _get_or_create_cart(current_user.id, db)

    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == item_in.product_id)
        .first()
    )
    if existing:
        new_qty = existing.quantity + item_in.quantity
        if new_qty > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock} units available (already have {existing.quantity})",
            )
        existing.quantity = new_qty
        db.commit()
        db.refresh(existing)
        return existing

    cart_item = CartItem(
        cart_id=cart.id,
        product_id=item_in.product_id,
        quantity=item_in.quantity,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


@router.put("/items/{item_id}", response_model=CartItemResponse, summary="Update cart item quantity")
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = _get_cart_item(item_id, current_user.id, db)

    if item_in.quantity > cart_item.product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {cart_item.product.stock} units available",
        )

    cart_item.quantity = item_in.quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove item from cart")
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = _get_cart_item(item_id, current_user.id, db)
    db.delete(cart_item)
    db.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Clear all items from cart")
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if cart:
        cart.items = []
        db.commit()


@router.get("/saved", response_model=list[SavedItemResponse], summary="List saved-for-later items")
def list_saved_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(SavedItem)
        .filter(SavedItem.user_id == current_user.id)
        .order_by(SavedItem.saved_at.desc())
        .all()
    )
    return items


@router.post("/saved", response_model=SavedItemResponse, status_code=status.HTTP_201_CREATED, summary="Move cart item to saved for later")
def save_cart_item(
    req: SaveCartItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = _get_cart_item(req.cart_item_id, current_user.id, db)

    existing_saved = (
        db.query(SavedItem)
        .filter(SavedItem.user_id == current_user.id, SavedItem.product_id == cart_item.product_id)
        .first()
    )
    if existing_saved:
        db.delete(cart_item)
        db.commit()
        return existing_saved

    saved = SavedItem(user_id=current_user.id, product_id=cart_item.product_id)
    db.add(saved)
    db.delete(cart_item)
    db.commit()
    db.refresh(saved)
    return saved


@router.post("/saved/{saved_id}/move-to-cart", response_model=CartItemResponse, summary="Move saved item back to cart")
def move_saved_to_cart(
    saved_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = (
        db.query(SavedItem)
        .filter(SavedItem.id == saved_id, SavedItem.user_id == current_user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved item not found")

    product = db.query(Product).filter(Product.id == saved.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    cart = _get_or_create_cart(current_user.id, db)

    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == saved.product_id)
        .first()
    )
    if existing:
        if existing.quantity + 1 > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock} units available (already have {existing.quantity})",
            )
        existing.quantity += 1
        db.delete(saved)
        db.commit()
        db.refresh(existing)
        return existing

    if 1 > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product is out of stock",
        )

    cart_item = CartItem(cart_id=cart.id, product_id=saved.product_id, quantity=1)
    db.add(cart_item)
    db.delete(saved)
    db.commit()
    db.refresh(cart_item)
    return cart_item


@router.delete("/saved/{saved_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove saved item")
def remove_saved_item(
    saved_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = (
        db.query(SavedItem)
        .filter(SavedItem.id == saved_id, SavedItem.user_id == current_user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved item not found")
    db.delete(saved)
    db.commit()


def _get_cart_item(item_id: int, user_id: int, db: Session) -> CartItem:
    cart_item = (
        db.query(CartItem)
        .join(Cart)
        .filter(CartItem.id == item_id, Cart.user_id == user_id)
        .first()
    )
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )
    return cart_item

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
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
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse, summary="Get current user cart")
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_id, items, total, created_at, updated_at = cart_service.get_cart(db, current_user.id)
    return CartResponse(id=cart_id, items=items, total=total, created_at=created_at, updated_at=updated_at)


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED, summary="Add item to cart (increments quantity if already present)")
def add_cart_item(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.add_cart_item(db, current_user.id, item_in.product_id, item_in.quantity)


@router.put("/items/{item_id}", response_model=CartItemResponse, summary="Update cart item quantity")
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.update_cart_item(db, current_user.id, item_id, item_in.quantity)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove item from cart")
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_service.remove_cart_item(db, current_user.id, item_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Clear all items from cart")
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_service.clear_cart(db, current_user.id)


@router.get("/saved", response_model=list[SavedItemResponse], summary="List saved-for-later items")
def list_saved_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.list_saved_items(db, current_user.id)


@router.post("/saved", response_model=SavedItemResponse, status_code=status.HTTP_201_CREATED, summary="Move cart item to saved for later")
def save_cart_item(
    req: SaveCartItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.save_cart_item(db, current_user.id, req.cart_item_id)


@router.post("/saved/{saved_id}/move-to-cart", response_model=CartItemResponse, summary="Move saved item back to cart")
def move_saved_to_cart(
    saved_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.move_saved_to_cart(db, current_user.id, saved_id)


@router.delete("/saved/{saved_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove saved item")
def remove_saved_item(
    saved_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_service.remove_saved_item(db, current_user.id, saved_id)

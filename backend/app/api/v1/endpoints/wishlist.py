from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.models.wishlist import WishlistItem
from app.schemas.cart import CartProductInfo
from app.schemas.wishlist import WishlistItemCreate, WishlistItemResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=list[WishlistItemResponse], summary="List wishlist items")
def list_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == current_user.id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )
    product_ids = [i.product_id for i in items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()} if product_ids else {}
    return [
        WishlistItemResponse(
            id=item.id,
            product_id=item.product_id,
            product=CartProductInfo.model_validate(products.get(item.product_id)) if item.product_id in products else None,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED, summary="Add product to wishlist")
def add_to_wishlist(
    item_in: WishlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    existing = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == current_user.id,
            WishlistItem.product_id == item_in.product_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in wishlist",
        )

    item = WishlistItem(user_id=current_user.id, product_id=item_in.product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return WishlistItemResponse(
        id=item.id,
        product_id=item.product_id,
        product=CartProductInfo.model_validate(product),
        created_at=item.created_at,
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove item from wishlist")
def remove_from_wishlist(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(WishlistItem)
        .filter(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )
    db.delete(item)
    db.commit()

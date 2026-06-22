from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.review import Review
from app.models.product import Product
from app.models.user import User
from app.schemas.review import ReviewResponse
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/admin/reviews", tags=["admin"])


def _recalculate_product_rating(product_id: int, db: Session):
    from sqlalchemy import func
    stats = (
        db.query(func.avg(Review.rating), func.count(Review.id))
        .filter(Review.product_id == product_id)
        .first()
    )
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.rating = round(float(stats[0] or 0), 2)
        product.review_count = stats[1] or 0
        db.commit()


@router.get("", response_model=list[ReviewResponse])
def list_all_reviews(
    product_id: int | None = Query(None),
    user_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(Review)
    if product_id:
        query = query.filter(Review.product_id == product_id)
    if user_id:
        query = query.filter(Review.user_id == user_id)
    return query.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    product_id = review.product_id
    db.delete(review)
    db.commit()
    _recalculate_product_rating(product_id, db)

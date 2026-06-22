from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["reviews"])


def _recalculate_product_rating(product_id: int, db: Session) -> None:
    stats = (
        db.query(
            func.coalesce(func.avg(Review.rating), 0),
            func.count(Review.id),
        )
        .filter(Review.product_id == product_id)
        .first()
    )
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.rating = round(float(stats[0]), 2)
        product.review_count = stats[1]
        db.flush()


@router.get("/products/{product_id}/reviews", response_model=list[ReviewResponse], summary="List reviews for a product")
def list_reviews(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, summary="Create a review for a product")
def create_review(
    product_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    existing = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.product_id == product_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )

    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(review)
    db.flush()
    _recalculate_product_rating(product_id, db)
    db.commit()
    db.refresh(review)
    return review


@router.put("/reviews/{review_id}", response_model=ReviewResponse, summary="Update own review")
def update_review(
    review_id: int,
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == current_user.id)
        .first()
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review_in.rating is not None:
        review.rating = review_in.rating
    if review_in.comment is not None:
        review.comment = review_in.comment

    db.flush()
    _recalculate_product_rating(review.product_id, db)
    db.commit()
    db.refresh(review)
    return review


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete own review")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == current_user.id)
        .first()
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    product_id = review.product_id
    db.delete(review)
    db.flush()
    _recalculate_product_rating(product_id, db)
    db.commit()

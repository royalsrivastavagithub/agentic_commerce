from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.services import review_service

router = APIRouter(tags=["reviews"])


@router.get("/products/{product_id}/reviews", response_model=list[ReviewResponse], summary="List reviews for a product")
def list_reviews(
    product_id: int,
    db: Session = Depends(get_db),
):
    return review_service.list_product_reviews(db, product_id)


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, summary="Create a review for a product")
def create_review(
    product_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return review_service.create_review(db, current_user.id, product_id, review_in.rating, review_in.comment)


@router.put("/reviews/{review_id}", response_model=ReviewResponse, summary="Update own review")
def update_review(
    review_id: int,
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return review_service.update_review(db, current_user.id, review_id, review_in.rating, review_in.comment)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete own review")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review_service.delete_review(db, current_user.id, review_id)

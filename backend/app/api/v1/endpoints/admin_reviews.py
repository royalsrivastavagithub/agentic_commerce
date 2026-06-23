from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ReviewResponse
from app.schemas.admin import AdminReviewsResponse
from app.api.deps import get_current_admin_user
from app.services.admin import review_service as admin_review_service

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


@router.get("", response_model=AdminReviewsResponse, summary="List all reviews (filterable by product)")
def list_all_reviews(
    product_id: int | None = Query(None),
    user_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    reviews, total, page, per_page = admin_review_service.list_all_reviews(
        db, product_id=product_id, user_id=user_id, page=page, per_page=per_page,
    )
    return AdminReviewsResponse(reviews=reviews, total=total, page=page, per_page=per_page)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a review (recalculates product rating)")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    admin_review_service.delete_review(db, review_id)

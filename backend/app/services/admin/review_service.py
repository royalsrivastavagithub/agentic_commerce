from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.review import Review
from app.services.review_service import recalculate_product_rating


def list_all_reviews(
    db: Session,
    product_id: int | None = None,
    user_id: int | None = None,
    page: int = 1,
    per_page: int = 20,
):
    query = db.query(Review)
    if product_id:
        query = query.filter(Review.product_id == product_id)
    if user_id:
        query = query.filter(Review.user_id == user_id)
    total = query.count()
    reviews = query.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return reviews, total, page, per_page


def delete_review(db: Session, review_id: int) -> None:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise NotFoundError("Review not found")
    product_id = review.product_id
    db.delete(review)
    db.commit()
    recalculate_product_rating(db, product_id)

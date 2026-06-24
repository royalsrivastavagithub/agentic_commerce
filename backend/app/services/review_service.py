from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from app.models.product import Product
from app.models.review import Review
from app.models.order import Order, OrderItem, OrderStatus
from app.services.product_service import get_product_by_id


def recalculate_product_rating(db: Session, product_id: int) -> None:
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


def list_product_reviews(db: Session, product_id: int, skip: int = 0, limit: int = 20) -> list[Review]:
    get_product_by_id(db, product_id)
    return (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_review(db: Session, user_id: int, product_id: int, rating: int, comment: str) -> Review:
    product = get_product_by_id(db, product_id)

    purchased = (
        db.query(Order)
        .join(OrderItem)
        .filter(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status == OrderStatus.DELIVERED,
        )
        .first()
    )
    if not purchased:
        raise ForbiddenError("You can only review products you have purchased")

    existing = (
        db.query(Review)
        .filter(Review.user_id == user_id, Review.product_id == product_id)
        .first()
    )
    if existing:
        raise ConflictError("You have already reviewed this product")

    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    db.flush()
    recalculate_product_rating(db, product_id)
    db.commit()
    db.refresh(review)
    return review


def update_review(db: Session, user_id: int, review_id: int, rating: int | None = None, comment: str | None = None) -> Review:
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == user_id)
        .first()
    )
    if not review:
        raise NotFoundError("Review not found")

    if rating is not None:
        review.rating = rating
    if comment is not None:
        review.comment = comment

    db.flush()
    recalculate_product_rating(db, review.product_id)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, user_id: int, review_id: int) -> None:
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == user_id)
        .first()
    )
    if not review:
        raise NotFoundError("Review not found")
    product_id = review.product_id
    db.delete(review)
    db.flush()
    recalculate_product_rating(db, product_id)
    db.commit()

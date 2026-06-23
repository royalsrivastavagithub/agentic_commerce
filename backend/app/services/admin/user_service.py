from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, BadRequestError
from app.models.order import Order
from app.models.user import User
from app.schemas.admin import AdminUserUpdate


def _compute_user_stats(db: Session, user_id: int) -> tuple[int, float]:
    stats = (
        db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0),
        )
        .filter(Order.user_id == user_id)
        .first()
    )
    return stats[0], float(stats[1])


def _build_admin_response(user: User, order_count: int, total_spent: float) -> dict:
    return dict(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        date_of_birth=user.date_of_birth,
        gender=user.gender,
        order_count=order_count,
        total_spent=total_spent,
    )


def list_users(db: Session, search: str = "", page: int = 1, per_page: int = 20):
    query = db.query(User)
    if search:
        like = f"%{search}%"
        query = query.filter(
            User.email.ilike(like)
            | User.first_name.ilike(like)
            | User.last_name.ilike(like)
        )
    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    results = []
    for user in users:
        order_count, total_spent = _compute_user_stats(db, user.id)
        results.append(_build_admin_response(user, order_count, total_spent))

    return results, total, page, per_page


def get_user(db: Session, user_id: int) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    order_count, total_spent = _compute_user_stats(db, user.id)
    return _build_admin_response(user, order_count, total_spent)


def update_user(db: Session, user_id: int, update_in: AdminUserUpdate) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    order_count, total_spent = _compute_user_stats(db, user.id)
    return _build_admin_response(user, order_count, total_spent)


def delete_user(db: Session, user_id: int, current_user_id: int) -> None:
    if user_id == current_user_id:
        raise BadRequestError("Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    db.delete(user)
    db.commit()

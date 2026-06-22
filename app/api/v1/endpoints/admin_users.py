from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.admin import AdminUserResponse, AdminUserUpdate
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("", response_model=list[AdminUserResponse])
def list_users(
    search: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
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
        stats = (
            db.query(
                func.count(Order.id),
                func.coalesce(func.sum(Order.total), 0),
            )
            .filter(Order.user_id == user.id)
            .first()
        )
        results.append(AdminUserResponse(
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
            order_count=stats[0],
            total_spent=float(stats[1]),
        ))

    return results


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stats = (
        db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0),
        )
        .filter(Order.user_id == user.id)
        .first()
    )

    return AdminUserResponse(
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
        order_count=stats[0],
        total_spent=float(stats[1]),
    )


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    update_in: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    stats = (
        db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0),
        )
        .filter(Order.user_id == user.id)
        .first()
    )

    return AdminUserResponse(
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
        order_count=stats[0],
        total_spent=float(stats[1]),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()

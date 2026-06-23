from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import AdminUserResponse, AdminUsersResponse, AdminUserUpdate
from app.api.deps import get_current_admin_user
from app.services.admin import user_service as admin_user_service

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=AdminUsersResponse, summary="List users with search and pagination")
def list_users(
    search: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    results, total, page, per_page = admin_user_service.list_users(db, search=search, page=page, per_page=per_page)
    return AdminUsersResponse(users=[AdminUserResponse(**r) for r in results], total=total, page=page, per_page=per_page)


@router.get("/{user_id}", response_model=AdminUserResponse, summary="Get user details with order stats")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return AdminUserResponse(**admin_user_service.get_user(db, user_id))


@router.patch("/{user_id}", response_model=AdminUserResponse, summary="Update a user (name, role, active status)")
def update_user(
    user_id: int,
    update_in: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return AdminUserResponse(**admin_user_service.update_user(db, user_id, update_in))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    admin_user_service.delete_user(db, user_id, current_user.id)

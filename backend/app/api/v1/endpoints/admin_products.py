from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.product import ProductSchema, ProductCreate, ProductUpdate
from app.api.deps import get_current_admin_user
from app.services.admin import product_service as admin_product_service

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED, response_model_by_alias=True, summary="Create a new product")
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_product_service.create_product(db, product_in)


@router.put("/{product_id}", response_model=ProductSchema, response_model_by_alias=True, summary="Update a product")
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_product_service.update_product(db, product_id, product_in)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a product")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    admin_product_service.delete_product(db, product_id)

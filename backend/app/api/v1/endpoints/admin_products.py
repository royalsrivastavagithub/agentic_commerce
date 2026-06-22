from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.models.category import Category
from app.schemas.product import ProductSchema, ProductCreate, ProductUpdate
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED, response_model_by_alias=True, summary="Create a new product")
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    data = product_in.model_dump(exclude_none=True)
    if not db.query(Category).filter(Category.id == data.get("category_id")).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with id {data['category_id']} not found",
        )
    try:
        product = Product(**data)
        db.add(product)
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this id or sku already exists",
        )
    return product


@router.put("/{product_id}", response_model=ProductSchema, response_model_by_alias=True, summary="Update a product")
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    update_data = product_in.model_dump(exclude_unset=True)
    if "category_id" in update_data and not db.query(Category).filter(Category.id == update_data["category_id"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with id {update_data['category_id']} not found",
        )
    for field, value in update_data.items():
        setattr(product, field, value)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update violates a unique constraint (id or sku)",
        )
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a product")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    db.delete(product)
    db.commit()

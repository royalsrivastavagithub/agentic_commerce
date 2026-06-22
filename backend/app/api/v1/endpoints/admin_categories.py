from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import CategorySchema, CategoryCreate, CategoryUpdate
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@router.post("", response_model=CategorySchema, status_code=status.HTTP_201_CREATED, summary="Create a new category")
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    existing = db.query(Category).filter(Category.name == category_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{category_in.name}' already exists",
        )
    category = Category(name=category_in.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategorySchema, summary="Update a category")
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )
    if category_in.name is not None:
        existing = (
            db.query(Category)
            .filter(Category.name == category_in.name, Category.id != category_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{category_in.name}' already exists",
            )
        category.name = category_in.name
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a category")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category with {product_count} product(s) referencing it. Reassign products first.",
        )
    db.delete(category)
    db.commit()

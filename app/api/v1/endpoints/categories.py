from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import CategorySchema, CategoryCreate, CategoryUpdate
from app.schemas.product import ProductsResponse
from app.api.deps import get_current_admin_user

router = APIRouter(tags=["categories"])


@router.get(
    "/categories",
    response_model=list[CategorySchema],
)
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.post(
    "/categories",
    response_model=CategorySchema,
    status_code=status.HTTP_201_CREATED,
)
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


@router.get(
    "/categories/{category_id}",
    response_model=CategorySchema,
)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )
    return category


@router.put(
    "/categories/{category_id}",
    response_model=CategorySchema,
)
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


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
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


@router.get(
    "/categories/{category_id}/products",
    response_model=ProductsResponse,
    response_model_by_alias=True,
)
def get_products_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )
    total = db.query(Product).filter(Product.category_id == category_id).count()
    products = (
        db.query(Product)
        .filter(Product.category_id == category_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)

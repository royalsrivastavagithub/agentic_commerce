from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategorySchema
from app.schemas.product import ProductsResponse
from app.services import product_service

router = APIRouter(tags=["categories"])


@router.get(
    "/categories",
    response_model=list[CategorySchema],
    summary="List all categories",
)
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return db.query(Category).order_by(Category.name).offset(skip).limit(limit).all()


@router.get(
    "/categories/{category_id}",
    response_model=CategorySchema,
    summary="Get category by ID",
)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )
    return category


@router.get(
    "/categories/{category_id}/products",
    response_model=ProductsResponse,
    response_model_by_alias=True,
    summary="List products by category with pagination",
)
def get_products_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    sort_by: str = Query("", pattern="^(|price|rating|title|discount|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_rating: float | None = Query(None, ge=0, le=5),
    min_discount: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )
    products, total = product_service.list_products(
        db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order,
        category_id=category_id, min_price=min_price, max_price=max_price,
        min_rating=min_rating, min_discount=min_discount,
    )
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategorySchema
from app.schemas.product import ProductsResponse

router = APIRouter(tags=["categories"])


@router.get(
    "/categories",
    response_model=list[CategorySchema],
    summary="List all categories",
)
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


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

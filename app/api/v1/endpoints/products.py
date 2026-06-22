from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductSchema, ProductsResponse

router = APIRouter(tags=["products"])


@router.get(
    "/products",
    response_model=ProductsResponse,
    response_model_by_alias=True,
    summary="List products with pagination",
)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    total = db.query(Product).count()
    products = db.query(Product).offset(skip).limit(limit).all()
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)


@router.get(
    "/products/search",
    response_model=ProductsResponse,
    response_model_by_alias=True,
    summary="Search products by title",
)
def search_products(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    q_like = f"%{q}%"
    total = db.query(Product).filter(Product.title.ilike(q_like)).count()
    products = (
        db.query(Product)
        .filter(Product.title.ilike(q_like))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)


@router.get(
    "/products/{product_id}",
    response_model=ProductSchema,
    response_model_by_alias=True,
    summary="Get product by ID",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product




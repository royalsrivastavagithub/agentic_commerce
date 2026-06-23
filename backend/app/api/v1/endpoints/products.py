from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product import ProductSchema, ProductsResponse
from app.services import product_service

router = APIRouter(tags=["products"])


@router.get(
    "/products/price-range",
    summary="Get min and max price across all products (optionally filtered)",
)
def get_price_range(
    q: str | None = Query(None, min_length=1),
    category_id: int | None = Query(None),
    min_discount: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    min_price, max_price = product_service.get_price_range(db, q=q, category_id=category_id, min_discount=min_discount)
    return {"min_price": min_price, "max_price": max_price}


@router.get(
    "/products",
    response_model=ProductsResponse,
    response_model_by_alias=True,
    summary="List products with pagination, sorting, and filters",
)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    sort_by: str = Query("", pattern="^(|price|rating)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_rating: float | None = Query(None, ge=0, le=5),
    min_discount: float | None = Query(None, ge=0, le=100),
    is_featured: bool | None = Query(None),
    db: Session = Depends(get_db),
):
    products, total = product_service.list_products(
        db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order,
        min_price=min_price, max_price=max_price, min_rating=min_rating,
        min_discount=min_discount, is_featured=is_featured,
    )
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)


@router.get(
    "/products/search",
    response_model=ProductsResponse,
    response_model_by_alias=True,
    summary="Search products by title or brand",
)
def search_products(
    q: str = Query(..., min_length=1),
    category_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    sort_by: str = Query("", pattern="^(|price|rating)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_rating: float | None = Query(None, ge=0, le=5),
    min_discount: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    products, total = product_service.search_products(
        db, q=q, category_id=category_id, skip=skip, limit=limit,
        sort_by=sort_by, sort_order=sort_order,
        min_price=min_price, max_price=max_price, min_rating=min_rating,
        min_discount=min_discount,
    )
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)


@router.get(
    "/products/featured",
    response_model=ProductsResponse,
    response_model_by_alias=True,
    summary="List featured products with pagination",
)
def get_featured_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(8, ge=1),
    db: Session = Depends(get_db),
):
    products, total = product_service.get_featured_products(db, skip=skip, limit=limit)
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)


@router.get(
    "/products/{product_id}",
    response_model=ProductSchema,
    response_model_by_alias=True,
    summary="Get product by ID",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product_by_id(db, product_id)

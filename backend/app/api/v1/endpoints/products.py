from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductSchema, ProductsResponse

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
    from sqlalchemy import func
    query = db.query(func.min(Product.price), func.max(Product.price))
    if q:
        safe_q = q.replace("%", "\\%").replace("_", "\\_")
        query = query.filter(or_(
            Product.title.ilike(f"%{safe_q}%", escape="\\"),
            Product.brand.ilike(f"%{safe_q}%", escape="\\"),
        ))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_discount is not None:
        query = query.filter(Product.discount_percentage >= min_discount)
    result = query.first()
    return {"min_price": result[0] or 0, "max_price": result[1] or 0}


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
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    if min_discount is not None:
        query = query.filter(Product.discount_percentage >= min_discount)

    total = query.count()

    if sort_by == "price":
        col = Product.price
    elif sort_by == "rating":
        col = Product.rating
    else:
        col = Product.id

    if sort_order == "desc":
        col = col.desc()
    else:
        col = col.asc()

    products = query.order_by(col).offset(skip).limit(limit).all()
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
    safe_q = q.replace("%", "\\%").replace("_", "\\_")
    like_pattern = f"%{safe_q}%"
    query = db.query(Product).filter(or_(
        Product.title.ilike(like_pattern, escape="\\"),
        Product.brand.ilike(like_pattern, escape="\\"),
    ))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    if min_discount is not None:
        query = query.filter(Product.discount_percentage >= min_discount)

    total = query.count()

    if sort_by == "price":
        col = Product.price
    elif sort_by == "rating":
        col = Product.rating
    else:
        col = Product.id

    if sort_order == "desc":
        col = col.desc()
    else:
        col = col.asc()

    products = query.order_by(col).offset(skip).limit(limit).all()
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
    total = db.query(Product).filter(Product.is_featured.is_(True)).count()
    products = db.query(Product).filter(Product.is_featured.is_(True)).offset(skip).limit(limit).all()
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

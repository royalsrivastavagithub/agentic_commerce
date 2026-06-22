from rapidfuzz import fuzz

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductSchema, ProductsResponse

router = APIRouter(tags=["products"])


def _score_product(q: str, p: Product) -> float:
    q_lower = q.lower()
    title = p.title.lower()
    desc = p.description.lower()
    brand = (p.brand or "").lower()

    scores = [
        fuzz.ratio(q_lower, title),
        fuzz.partial_ratio(q_lower, title) * 0.9,
        fuzz.partial_ratio(q_lower, desc) * 0.7,
    ]
    if brand:
        scores.append(fuzz.partial_ratio(q_lower, brand) * 0.6)

    return max(scores)


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
    summary="Search products with fuzzy matching",
)
def search_products(
    q: str = Query(..., min_length=1),
    category_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    base_query = db.query(Product)
    if category_id is not None:
        base_query = base_query.filter(Product.category_id == category_id)
    all_products = base_query.all()
    scored = [(p, _score_product(q, p)) for p in all_products]
    matched = [(p, s) for p, s in scored if s >= 40]
    matched.sort(key=lambda x: -x[1])

    total = len(matched)
    page = [p for p, _ in matched[skip:skip + limit]]
    return ProductsResponse(products=page, total=total, skip=skip, limit=limit)


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

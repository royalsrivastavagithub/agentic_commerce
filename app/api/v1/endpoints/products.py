from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductSchema, ProductCreate, ProductUpdate, ProductsResponse

router = APIRouter(tags=["products"])
categories_router = APIRouter(tags=["categories"])


@router.get(
    "/products",
    response_model=ProductsResponse,
    response_model_by_alias=True,
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
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product


@router.post(
    "/products",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    data = product_in.model_dump(exclude_none=True)
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


@router.put(
    "/products/{product_id}",
    response_model=ProductSchema,
    response_model_by_alias=True,
)
def update_product(
    product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    update_data = product_in.model_dump(exclude_unset=True)
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


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    db.delete(product)
    db.commit()


@categories_router.get(
    "/categories",
    response_model=list[str],
)
def get_categories(db: Session = Depends(get_db)):
    results = (
        db.query(Product.category).distinct().order_by(Product.category).all()
    )
    return [r[0] for r in results]


@categories_router.get(
    "/categories/{category_name}",
    response_model=ProductsResponse,
    response_model_by_alias=True,
)
def get_products_by_category(
    category_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    total = db.query(Product).filter(Product.category == category_name).count()
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category_name}' not found",
        )
    products = (
        db.query(Product)
        .filter(Product.category == category_name)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return ProductsResponse(products=products, total=total, skip=skip, limit=limit)

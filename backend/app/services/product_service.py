from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.product import Product


def _apply_filters(
    db: Session,
    *,
    q: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    min_discount: float | None = None,
    is_featured: bool | None = None,
):
    query = db.query(Product)

    if q:
        safe_q = q.replace("%", "\\%").replace("_", "\\_")
        query = query.filter(or_(
            Product.title.ilike(f"%{safe_q}%", escape="\\"),
            Product.brand.ilike(f"%{safe_q}%", escape="\\"),
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
    if is_featured is not None:
        query = query.filter(Product.is_featured.is_(is_featured))

    return query


def _apply_sorting(query, sort_by: str = "", sort_order: str = "asc"):
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

    return query.order_by(col)


def _paginate(query, skip: int, limit: int):
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def list_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "",
    sort_order: str = "asc",
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    min_discount: float | None = None,
    is_featured: bool | None = None,
):
    query = _apply_filters(
        db,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        min_discount=min_discount,
        is_featured=is_featured,
    )
    query = _apply_sorting(query, sort_by, sort_order)
    return _paginate(query, skip, limit)


def search_products(
    db: Session,
    q: str,
    category_id: int | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "",
    sort_order: str = "asc",
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    min_discount: float | None = None,
):
    query = _apply_filters(
        db,
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        min_discount=min_discount,
    )
    query = _apply_sorting(query, sort_by, sort_order)
    return _paginate(query, skip, limit)


def get_featured_products(db: Session, skip: int = 0, limit: int = 8):
    query = db.query(Product).filter(Product.is_featured.is_(True))
    return _paginate(query, skip, limit)


def get_product_by_id(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError(f"Product with id {product_id} not found")
    return product


def get_price_range(
    db: Session,
    q: str | None = None,
    category_id: int | None = None,
    min_discount: float | None = None,
):
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
    return (result[0] or 0, result[1] or 0)

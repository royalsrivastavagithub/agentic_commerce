from typing import Any, Self

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.product import Product

SORT_COLUMNS = {
    "price": Product.price,
    "rating": Product.rating,
    "title": Product.title,
    "discount": Product.discount_percentage,
    "created_at": Product.id,
}


class ProductQueryBuilder:
    def __init__(self, db: Session):
        self._query = db.query(Product)

    def with_search(self, q: str | None) -> Self:
        if q:
            safe_q = q.replace("%", "\\%").replace("_", "\\_")
            self._query = self._query.filter(or_(
                Product.title.ilike(f"%{safe_q}%", escape="\\"),
                Product.brand.ilike(f"%{safe_q}%", escape="\\"),
            ))
        return self

    def with_category(self, category_id: int | None) -> Self:
        if category_id is not None:
            self._query = self._query.filter(Product.category_id == category_id)
        return self

    def with_price_min(self, min_price: float | None) -> Self:
        if min_price is not None:
            self._query = self._query.filter(Product.price >= min_price)
        return self

    def with_price_max(self, max_price: float | None) -> Self:
        if max_price is not None:
            self._query = self._query.filter(Product.price <= max_price)
        return self

    def with_price_range(self, min_price: float | None, max_price: float | None) -> Self:
        return self.with_price_min(min_price).with_price_max(max_price)

    def with_min_rating(self, min_rating: float | None) -> Self:
        if min_rating is not None:
            self._query = self._query.filter(Product.rating >= min_rating)
        return self

    def with_min_discount(self, min_discount: float | None) -> Self:
        if min_discount is not None:
            self._query = self._query.filter(Product.discount_percentage >= min_discount)
        return self

    def with_featured(self, is_featured: bool | None) -> Self:
        if is_featured is not None:
            self._query = self._query.filter(Product.is_featured.is_(is_featured))
        return self

    def sort_by(self, field: str = "", order: str = "asc") -> Self:
        col = SORT_COLUMNS.get(field, Product.id)
        self._query = self._query.order_by(col.desc() if order == "desc" else col.asc())
        return self

    def paginate(self, skip: int, limit: int) -> tuple[list[Product], int]:
        total = self._query.count()
        items = self._query.offset(skip).limit(limit).all()
        return items, total

    def aggregate(self, *columns: Any) -> Any:
        return self._query.with_entities(*columns).first()

    @property
    def query(self):
        return self._query


# ── Thin wrappers (backward-compatible API) ─────────────────────────

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
    return (
        ProductQueryBuilder(db)
        .with_category(category_id)
        .with_price_range(min_price, max_price)
        .with_min_rating(min_rating)
        .with_min_discount(min_discount)
        .with_featured(is_featured)
        .sort_by(sort_by, sort_order)
        .paginate(skip, limit)
    )


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
    is_featured: bool | None = None,
):
    return (
        ProductQueryBuilder(db)
        .with_search(q)
        .with_category(category_id)
        .with_price_range(min_price, max_price)
        .with_min_rating(min_rating)
        .with_min_discount(min_discount)
        .with_featured(is_featured)
        .sort_by(sort_by, sort_order)
        .paginate(skip, limit)
    )


def get_featured_products(db: Session, skip: int = 0, limit: int = 8):
    return (
        ProductQueryBuilder(db)
        .with_featured(True)
        .paginate(skip, limit)
    )


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
    result = (
        ProductQueryBuilder(db)
        .with_search(q)
        .with_category(category_id)
        .with_min_discount(min_discount)
        .aggregate(func.min(Product.price), func.max(Product.price))
    )
    return (result[0] or 0, result[1] or 0)

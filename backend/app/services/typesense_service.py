import logging
import re
import typesense
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)
from app.models.product import Product
from app.models.category import Category


_client = None


def get_client() -> typesense.Client | None:
    global _client
    if _client is None and settings.TYPESENSE_ENABLED:
        try:
            _client = typesense.Client({
                "nodes": [{
                    "host": settings.TYPESENSE_HOST,
                    "port": settings.TYPESENSE_PORT,
                    "protocol": settings.TYPESENSE_PROTOCOL,
                }],
                "api_key": settings.TYPESENSE_API_KEY,
                "connection_timeout_seconds": 2,
            })
        except Exception as e:
            logger.error("Typesense connection failed: %s", e)
            _client = None
    return _client


PRODUCTS_SCHEMA = {
    "name": "products",
    "fields": [
        {"name": "title", "type": "string", "infix": True},
        {"name": "description", "type": "string", "infix": True},
        {"name": "brand", "type": "string", "infix": True},
        {"name": "category", "type": "string", "facet": True},
        {"name": "price", "type": "float"},
        {"name": "rating", "type": "float"},
        {"name": "stock", "type": "int32"},
        {"name": "discount_percentage", "type": "float"},
        {"name": "review_count", "type": "int32"},
        {"name": "availability_status", "type": "string"},
        {"name": "in_stock", "type": "bool", "facet": True},
    ],
    "default_sorting_field": "rating",
}


def ensure_collection() -> bool:
    client = get_client()
    if not client:
        return False
    try:
        client.collections["products"].retrieve()
        return True
    except typesense.exceptions.ObjectNotFound:
        client.collections.create(PRODUCTS_SCHEMA)
        logger.info("Created Typesense 'products' collection")
        return True
    except Exception as e:
        logger.error("Typesense ensure_collection error: %s", e)
        return False


def _product_to_document(p: Product) -> dict:
    return {
        "id": str(p.id),
        "title": p.title,
        "description": p.description or "",
        "brand": p.brand or "",
        "category": p.category,
        "price": p.price,
        "rating": p.rating,
        "stock": p.stock,
        "discount_percentage": p.discount_percentage,
        "review_count": p.review_count,
        "availability_status": p.availability_status,
        "in_stock": p.availability_status == "In Stock",
    }


def reindex_all(db: Session) -> int:
    client = get_client()
    if not client:
        return 0
    try:
        client.collections["products"].delete()
    except Exception:
        pass
    client.collections.create(PRODUCTS_SCHEMA)

    products = db.query(Product).all()
    documents = [_product_to_document(p) for p in products]
    result = client.collections["products"].documents.import_(documents)
    imported = len(documents)
    logger.info("Indexed %d products to Typesense", imported)
    return imported


def _build_filter_by(
    category: str | None = None,
    in_stock: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    min_discount: float | None = None,
) -> str:
    parts = []
    if in_stock is True:
        parts.append("in_stock:true")
    elif in_stock is False:
        parts.append("in_stock:false")
    if category:
        parts.append(f"category:={category}")
    if min_price is not None:
        parts.append(f"price:>={min_price}")
    if max_price is not None:
        parts.append(f"price:<={max_price}")
    if min_rating is not None:
        parts.append(f"rating:>={min_rating}")
    if min_discount is not None:
        parts.append(f"discount_percentage:>={min_discount}")
    return " && ".join(parts)


SORT_MAP = {
    "price": "price",
    "rating": "rating",
    "discount": "discount_percentage",
    "review_count": "review_count",
    "created_at": "id",
    "stock": "stock",
    "title": "title",
}


def search_products(
    query: str,
    category: str | None = None,
    in_stock: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    min_discount: float | None = None,
    sort_by: str = "",
    sort_order: str = "asc",
    per_page: int = 20,
) -> tuple[list[dict], int]:
    client = get_client()
    if not client:
        return [], 0

    filter_by = _build_filter_by(category, in_stock, min_price, max_price, min_rating, min_discount)

    ts_sort = ""
    if sort_by:
        col = SORT_MAP.get(sort_by, sort_by)
        ts_sort = f"{col}:{sort_order}"

    search_params = {
        "q": query,
        "query_by": "title,brand,description",
        "infix": "always",
        "filter_by": filter_by or "",
        "sort_by": ts_sort or "",
        "per_page": str(per_page),
    }

    try:
        result = client.collections["products"].documents.search(search_params)
        hits = result.get("hits", [])
        total = result.get("found", 0)
    except Exception as e:
        logger.warning("Typesense search error: %s", e)
        hits, total = [], 0

    if not hits and len(query) >= 4:
        try:
            search_params["infix"] = "off"
            search_params["num_typos"] = "2"
            result2 = client.collections["products"].documents.search(search_params)
            hits2 = result2.get("hits", [])
            total2 = result2.get("found", 0)
            if hits2:
                hits, total = hits2, total2
        except Exception as e:
            logger.warning("Typesense typo fallback error: %s", e)
        finally:
            search_params["infix"] = "always"
            search_params.pop("num_typos", None)

    if len(query) > 2 and query[-1].lower() == "s":
        seen_ids = {h["document"]["id"] for h in hits}
        merged = list(hits)

        def _try_singular(s: str) -> bool:
            nonlocal hits, total, seen_ids, merged
            if s == query or not s:
                return False
            try:
                search_params["q"] = s
                r = client.collections["products"].documents.search(search_params)
                h2 = r.get("hits", [])
                t2 = r.get("found", 0)
                new_ids = {h["document"]["id"] for h in h2} - seen_ids
                if not new_ids:
                    return False
                for h in h2:
                    if h["document"]["id"] not in seen_ids:
                        merged.append(h)
                        seen_ids.add(h["document"]["id"])
                if t2 > total:
                    total = t2
                if len(merged) > len(hits):
                    hits = merged
                return True
            except Exception as e:
                logger.warning("Typesense search error (plural fallback): %s", e)
                return False

        # Try stripping just "s" first (phones → phone)
        if not _try_singular(query[:-1]):
            # Fall back to stripping "es" (watches → watch)
            if query.endswith("es"):
                _try_singular(query[:-2])

    docs = [h["document"] for h in hits]

    # Post-filter via substring check (Typesense infix uses N-grams which
    # can produce false positives — e.g. "watches" trigram-matches "matches").
    # Check that at least one query token appears as a substring in a searched field.
    tokens = query.lower().split()
    candidates = set(tokens)
    for t in tokens:
        if len(t) > 2 and t[-1] == "s":
            candidates.add(t[:-1])
            if t.endswith("es"):
                candidates.add(t[:-2])
    text_by_doc = {}
    for d in docs:
        text = " ".join((
            d.get("title", "") or "",
            d.get("description", "") or "",
            d.get("brand", "") or "",
        )).lower()
        text_by_doc[d["id"]] = text
    docs = [d for d in docs if any(c in text_by_doc[d["id"]] for c in candidates)]
    total = len(docs)

    return docs, total

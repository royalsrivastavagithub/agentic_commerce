import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.limiter import limiter
from app.db.session import engine, Base
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from app.services.typesense_service import ensure_collection, reindex_all
from app.db.session import SessionLocal as _SessionLocal

AUTO_SEED_ENABLED = True
logger = logging.getLogger(__name__)


def _seed_users():
    SEED_USERS = [
        {
            "email": "admin@admin.com",
            "password": "admin",
            "role": "admin",
            "first_name": "Admin",
            "last_name": "User",
        },
        {
            "email": "test@test.com",
            "password": "test",
            "role": "user",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1-555-123-4567",
            "gender": "male",
        },
    ]
    db = Session(bind=engine)
    try:
        for data in SEED_USERS:
            existing = db.query(User).filter(User.email == data["email"]).first()
            if not existing:
                user = User(
                    email=data["email"],
                    hashed_password=get_password_hash(data["password"]),
                    role=data["role"],
                    is_active=True,
                    is_verified=True,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    phone=data.get("phone"),
                    gender=data.get("gender"),
                )
                db.add(user)
        db.commit()
    finally:
        db.close()


def _migrate_conversations():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE conversations ADD COLUMN state_json TEXT DEFAULT '{}'"))
            conn.commit()
    except Exception:
        pass


REVIEW_COMMENTS = [
    "Great product, very satisfied!",
    "Good quality for the price.",
    "Works as expected, happy with purchase.",
    "Decent product, could be better.",
    "Average quality, nothing special.",
    "Not bad, but there are better options.",
    "Excellent quality, highly recommend!",
    "Love this! Will buy again.",
    "Pretty good overall.",
    "Does the job, no complaints.",
    "Amazing product, exceeded expectations!",
    "Okay for the price point.",
    "Solid build quality, recommended.",
    "Fantastic! Best purchase this year.",
    "Exactly what I needed.",
    "Good value for money.",
    "Pleased with this purchase.",
    "Would recommend to a friend.",
]


CAMEL_TO_SNAKE = {
    "discountPercentage": "discount_percentage",
    "warrantyInformation": "warranty_information",
    "shippingInformation": "shipping_information",
    "availabilityStatus": "availability_status",
    "returnPolicy": "return_policy",
    "minimumOrderQuantity": "minimum_order_quantity",
}
PRODUCT_SIMPLE_FIELDS = {
    "id", "title", "description", "price", "rating",
    "stock", "tags", "brand", "sku", "weight",
    "dimensions", "meta", "images", "thumbnail",
}


def _seed_catalog():
    from app.models.product import Product
    from app.models.category import Category

    db = Session(bind=engine)
    try:
        if db.query(Product).count() > 0:
            logger.info("Products already seeded, skipping catalog seed")
            return

        import json
        import random
        from datetime import datetime, timezone
        from pathlib import Path

        data_dir = Path(__file__).resolve().parent.parent / "data"
        with open(data_dir / "new_products.json") as f:
            source = json.load(f)["products"]

        logger.info("Seeding %d products...", len(source))

        # ── Categories ─────────────────────────────────────────────
        cat_names = sorted({p["category"] for p in source})
        cat_mapping = {}
        for name in cat_names:
            cat = db.query(Category).filter(Category.name == name).first()
            if not cat:
                cat = Category(name=name)
                db.add(cat)
                db.flush()
            cat_mapping[name] = cat.id
        logger.info("Created %d categories", len(cat_mapping))

        # ── Products ───────────────────────────────────────────────
        FEATURED_COUNT = 10
        created = 0
        for i, p in enumerate(source):
            cat_id = cat_mapping.get(p.get("category"))
            if cat_id is None:
                continue
            prod_data = {}
            for k, v in p.items():
                if k in ("category",):
                    continue
                if k in PRODUCT_SIMPLE_FIELDS:
                    prod_data[k] = v
                elif k in CAMEL_TO_SNAKE:
                    prod_data[CAMEL_TO_SNAKE[k]] = v
            prod_data["category_id"] = cat_id
            prod_data["is_featured"] = i < FEATURED_COUNT
            db.add(Product(**prod_data))
            created += 1
        db.commit()
        logger.info("Created %d products", created)

        # ── Create test users ───────────────────────────────────────
        from datetime import date
        TEST_USERS = [
            {"email": "alice@test.com",   "first_name": "Alice",   "last_name": "Johnson",  "phone": "9876543210", "gender": "female"},
            {"email": "bob@test.com",     "first_name": "Bob",     "last_name": "Smith",    "phone": "9876543211", "gender": "male"},
            {"email": "charlie@test.com", "first_name": "Charlie", "last_name": "Brown",    "phone": "9876543212", "gender": "male"},
            {"email": "diana@test.com",   "first_name": "Diana",   "last_name": "Prince",   "phone": "9876543213", "gender": "female"},
            {"email": "eve@test.com",     "first_name": "Eve",     "last_name": "Davis",    "phone": "9876543214", "gender": "female"},
        ]
        for info in TEST_USERS:
            existing = db.query(User).filter(User.email == info["email"]).first()
            if not existing:
                db.add(User(
                    email=info["email"],
                    hashed_password=get_password_hash("test123"),
                    first_name=info["first_name"],
                    last_name=info["last_name"],
                    phone=info["phone"],
                    gender=info["gender"],
                    date_of_birth=date(1990, 1, 1),
                    is_active=True,
                    is_verified=True,
                    role="user",
                ))
        db.commit()

        # ── Orders & Reviews ───────────────────────────────────────
        from app.models.address import Address
        from app.models.order import Order, OrderItem, OrderStatus
        from app.models.review import Review

        test_users = db.query(User).filter(User.role == "user").all()
        rng = random.Random(42)

        for user in test_users:
            addr = Address(
                user_id=user.id,
                label="Home",
                street=f"{rng.randint(1, 999)} Test Street",
                city=rng.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]),
                state=rng.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]),
                pincode=str(rng.randint(100000, 999999)),
                country="India",
                is_default=True,
                address_type="both",
            )
            db.add(addr)

        db.commit()

        shuffled = rng.sample(source, len(source))
        order_count = 0
        review_count = 0
        idx = 0

        for user in test_users:
            for _ in range(5):
                num_items = rng.randint(3, 6)
                items_in_order = shuffled[idx : idx + num_items]
                idx += num_items
                if not items_in_order or idx > len(shuffled):
                    break

                order_items_data = []
                subtotal = 0
                for prod in items_in_order:
                    qty = rng.randint(1, 2)
                    line_total = round(prod["price"] * qty, 2)
                    subtotal += line_total
                    order_items_data.append((prod, qty, line_total))

                subtotal = round(subtotal, 2)
                order = Order(
                    user_id=user.id,
                    total=subtotal,
                    subtotal=subtotal,
                    status=OrderStatus.DELIVERED,
                    shipping_name=f"{user.first_name} Test",
                    shipping_phone=f"99999{rng.randint(10000, 99999)}",
                    shipping_address_line_1=f"{rng.randint(1, 999)} Test Street",
                    shipping_city=rng.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]),
                    shipping_state=rng.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]),
                    shipping_country="India",
                    shipping_pincode=str(rng.randint(100000, 999999)),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(order)
                db.flush()

                for prod, qty, line_total in order_items_data:
                    db.add(OrderItem(
                        order_id=order.id,
                        product_id=prod["id"],
                        product_name=prod["title"],
                        product_price=prod["price"],
                        quantity=qty,
                        subtotal=line_total,
                        thumbnail=prod.get("thumbnail", ""),
                    ))

                    existing_review = (
                        db.query(Review)
                        .filter(Review.user_id == user.id, Review.product_id == prod["id"])
                        .first()
                    )
                    if not existing_review:
                        rating = rng.choices([1, 2, 3, 4, 5], weights=[1, 2, 4, 5, 3])[0]
                        comment = rng.choice(REVIEW_COMMENTS)
                        db.add(Review(
                            user_id=user.id,
                            product_id=prod["id"],
                            rating=rating,
                            comment=comment,
                            created_at=datetime.now(timezone.utc),
                        ))
                        review_count += 1

                order_count += 1

        db.commit()
        logger.info("Seeded %d orders and %d reviews", order_count, review_count)

        # ── Recalculate Ratings ────────────────────────────────────
        from sqlalchemy import func
        updated = 0
        for product in db.query(Product).all():
            stats = (
                db.query(func.avg(Review.rating), func.count(Review.id))
                .filter(Review.product_id == product.id)
                .first()
            )
            avg_rating = round(float(stats[0] or 0), 2)
            rev_count = stats[1] or 0
            if product.rating != avg_rating or product.review_count != rev_count:
                product.rating = avg_rating
                product.review_count = rev_count
                updated += 1
        db.commit()
        logger.info("Recalculated ratings for %d products", updated)

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_conversations()
    _seed_users()
    if AUTO_SEED_ENABLED:
        _seed_catalog()
    if settings.TYPESENSE_ENABLED:
        if ensure_collection():
            from app.db.session import SessionLocal
            from app.models.product import Product
            db = SessionLocal()
            try:
                total = db.query(Product).count()
                if total > 0:
                    count = reindex_all(db)
                    logger.info("Typesense auto-indexed %d products", count)
            finally:
                db.close()
    yield


openapi_tags = [
    {"name": "healthcheck", "description": "API health and status checks"},
    {"name": "auth", "description": "User registration, email verification, login, token management, and profile management"},
    {"name": "products", "description": "Browse and search the product catalog (public)"},
    {"name": "categories", "description": "Browse product categories (public)"},
    {"name": "addresses", "description": "Manage user shipping and billing addresses"},
    {"name": "cart", "description": "Manage shopping cart items (add, update quantity, remove, clear)"},
    {"name": "orders", "description": "Place orders (checkout) and view/cancel order history"},
    {"name": "wishlist", "description": "Manage product wishlist"},
    {"name": "reviews", "description": "Create, update, and delete product reviews"},
    {"name": "admin-orders", "description": "Admin: view all orders and update order status"},
    {"name": "admin-products", "description": "Admin: create, update, and delete products"},
    {"name": "admin-categories", "description": "Admin: create, update, and delete categories"},
    {"name": "admin-users", "description": "Admin: list, search, update, and delete user accounts"},
    {"name": "admin-reviews", "description": "Admin: list and delete product reviews"},
    {"name": "admin-dashboard", "description": "Admin: dashboard metrics, revenue analytics, top products, recent orders and users"},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Agentic Commerce. Provides a complete e-commerce backend with product catalog, user management, cart, orders, reviews, wishlist, and a full admin dashboard with analytics.",
    version="0.1.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEV else None,
    redoc_url="/redoc" if settings.DEV else None,
    openapi_url="/openapi.json" if settings.DEV else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


if settings.DEV:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.PROJECT_NAME,
            version="0.1.0",
            description="Backend API for Agentic Commerce. Provides a complete e-commerce backend with product catalog, user management, cart, orders, reviews, wishlist, and a full admin dashboard with analytics.",
            routes=app.routes,
            tags=openapi_tags,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT access token. Get one from **POST /api/v1/auth/login** or **POST /api/v1/auth/login/access-token**.",
            }
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Agentic Commerce API. Healthcheck is available at /api/v1/health"}


def main():
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run("app.main:app", port=8000, reload=reload_enabled)


if __name__ == "__main__":
    main()

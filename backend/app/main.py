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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_users()
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
    return response


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
    uvicorn.run("app.main:app", port=8000, reload=True)


if __name__ == "__main__":
    main()

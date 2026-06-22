import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.v1.router import api_router
from app.core.config import settings

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
)


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

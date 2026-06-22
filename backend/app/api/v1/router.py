from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.addresses import router as addresses_router
from app.api.v1.endpoints.cart import router as cart_router
from app.api.v1.endpoints.orders import router as orders_router
from app.api.v1.endpoints.admin_orders import router as admin_orders_router
from app.api.v1.endpoints.wishlist import router as wishlist_router
from app.api.v1.endpoints.reviews import router as reviews_router
from app.api.v1.endpoints.admin_users import router as admin_users_router
from app.api.v1.endpoints.admin_reviews import router as admin_reviews_router
from app.api.v1.endpoints.admin_dashboard import router as admin_dashboard_router
from app.api.v1.endpoints.admin_products import router as admin_products_router
from app.api.v1.endpoints.admin_categories import router as admin_categories_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(categories_router)
api_router.include_router(addresses_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(admin_orders_router)
api_router.include_router(wishlist_router)
api_router.include_router(reviews_router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_reviews_router)
api_router.include_router(admin_dashboard_router)
api_router.include_router(admin_products_router)
api_router.include_router(admin_categories_router)
api_router.include_router(webhooks_router)


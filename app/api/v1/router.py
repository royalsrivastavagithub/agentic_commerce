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


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    DashboardSummary,
    RevenuePoint,
    TopProduct,
    RecentOrder,
    RecentUser,
)
from app.api.deps import get_current_admin_user
from app.services.admin import dashboard_service

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Dashboard summary metrics")
def dashboard_summary(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return DashboardSummary(**dashboard_service.get_summary(db))


@router.get("/revenue-over-time", response_model=list[RevenuePoint], summary="Revenue breakdown by day")
def revenue_over_time(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return [RevenuePoint(**r) for r in dashboard_service.get_revenue_over_time(db, days=days)]


@router.get("/top-products", response_model=list[TopProduct], summary="Top selling products")
def top_products(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return [TopProduct(**r) for r in dashboard_service.get_top_products(db, limit=limit)]


@router.get("/recent-orders", response_model=list[RecentOrder], summary="Most recent orders")
def recent_orders(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return [RecentOrder(**r) for r in dashboard_service.get_recent_orders(db, limit=limit)]


@router.get("/recent-users", response_model=list[RecentUser], summary="Most recently registered users")
def recent_users(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return [RecentUser(**r) for r in dashboard_service.get_recent_users(db, limit=limit)]

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User


def get_summary(db: Session):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.status != OrderStatus.CANCELLED
    ).scalar() or 0
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    status_counts: dict[str, int] = {}
    for s in OrderStatus:
        count = db.query(func.count(Order.id)).filter(Order.status == s).scalar() or 0
        if count > 0:
            status_counts[s.value] = count

    low_stock_count = db.query(func.count(Product.id)).filter(Product.stock < 10).scalar() or 0

    return dict(
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        avg_order_value=avg_order_value,
        orders_by_status=status_counts,
        low_stock_count=low_stock_count,
    )


def get_revenue_over_time(db: Session, days: int = 30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = (
        db.query(
            func.date(Order.created_at).label("date"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .filter(Order.created_at >= cutoff, Order.status != OrderStatus.CANCELLED)
        .group_by(func.date(Order.created_at))
        .order_by("date")
        .all()
    )
    return [{"date": r[0], "revenue": float(r[1])} for r in results]


def get_top_products(db: Session, limit: int = 10):
    results = (
        db.query(
            OrderItem.product_id,
            Product.title,
            func.sum(OrderItem.quantity).label("total_qty"),
            func.sum(OrderItem.subtotal).label("total_rev"),
        )
        .join(Product, OrderItem.product_id == Product.id)
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [
        dict(id=r[0], title=r[1], total_quantity=int(r[2] or 0), total_revenue=float(r[3] or 0))
        for r in results
    ]


def get_recent_orders(db: Session, limit: int = 10):
    orders = (
        db.query(Order, User.email)
        .join(User, Order.user_id == User.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        dict(id=o.Order.id, user_id=o.Order.user_id, user_email=o.email,
             status=o.Order.status, total=o.Order.total, created_at=o.Order.created_at)
        for o in orders
    ]


def get_recent_users(db: Session, limit: int = 10):
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .limit(limit)
        .all()
    )
    return [
        dict(id=u.id, email=u.email, first_name=u.first_name, last_name=u.last_name,
             is_active=u.is_active, created_at=None)
        for u in users
    ]

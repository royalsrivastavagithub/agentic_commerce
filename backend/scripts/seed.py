"""
Unified seed script: products, admin, test users, orders, and reviews.

Usage:
    python scripts/seed.py              # seed if DB is empty
    python scripts/seed.py --force      # clear and re-seed everything
    python scripts/seed.py --products-only  # seed products only
"""

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.address import Address
from app.models.order import Order, OrderItem, OrderStatus
from app.models.review import Review

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRODUCTS_FILE = DATA_DIR / "new_products.json"
API_PREFIX = "/api/v1"
FEATURED_COUNT = 10
RANDOM_SEED = 42

# ── Test users ──────────────────────────────────────────────────────────
TEST_USERS = [
    {"email": "alice@test.com",   "first_name": "Alice",   "last_name": "Johnson",  "phone": "9876543210", "gender": "female", "password": "test123"},
    {"email": "bob@test.com",     "first_name": "Bob",     "last_name": "Smith",    "phone": "9876543211", "gender": "male",   "password": "test123"},
    {"email": "charlie@test.com", "first_name": "Charlie", "last_name": "Brown",    "phone": "9876543212", "gender": "male",   "password": "test123"},
    {"email": "diana@test.com",   "first_name": "Diana",   "last_name": "Prince",   "phone": "9876543213", "gender": "female", "password": "test123"},
    {"email": "eve@test.com",     "first_name": "Eve",     "last_name": "Davis",    "phone": "9876543214", "gender": "female", "password": "test123"},
]

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


# ── Helpers ─────────────────────────────────────────────────────────────

def _load_products() -> list[dict]:
    with open(PRODUCTS_FILE) as f:
        return json.load(f)["products"]


def _get_or_create_admin(db) -> User:
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        from datetime import date
        admin = User(
            email="admin@admin.com",
            first_name="Admin",
            last_name="User",
            phone="9999999999",
            date_of_birth=date(1990, 1, 1),
            gender="other",
            hashed_password=get_password_hash("admin"),
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"  Created admin: admin@admin.com (id={admin.id})")
    else:
        print(f"  Using existing admin: {admin.email} (id={admin.id})")
    return admin


def _create_test_users(db) -> list[User]:
    users = []
    for info in TEST_USERS:
        user = db.query(User).filter(User.email == info["email"]).first()
        if not user:
            from datetime import date
            dob = date(1990, 1, 1)
            user = User(
                email=info["email"],
                first_name=info["first_name"],
                last_name=info["last_name"],
                phone=info["phone"],
                date_of_birth=dob,
                gender=info["gender"],
                hashed_password=get_password_hash(info["password"]),
                is_active=True,
                is_verified=True,
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  Created user: {info['email']} (id={user.id})")
        else:
            print(f"  Using existing user: {info['email']} (id={user.id})")

        # Ensure each user has at least one address
        rng_addr = random.Random(user.id)
        addr = db.query(Address).filter(Address.user_id == user.id).first()
        if not addr:
            addr = Address(
                user_id=user.id,
                label="Home",
                street=f"{rng_addr.randint(1, 999)} Test Street",
                city=rng_addr.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]),
                state=rng_addr.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]),
                pincode=str(rng_addr.randint(100000, 999999)),
                country="India",
                is_default=True,
                address_type="both",
            )
            db.add(addr)
            db.commit()
        users.append(user)
    return users


# ── Product seeding (via API) ───────────────────────────────────────────

def _seed_categories(client, headers, products) -> dict[str, int]:
    names = sorted({p["category"] for p in products})
    mapping = {}
    for name in names:
        resp = client.post(f"{API_PREFIX}/admin/categories", json={"name": name}, headers=headers)
        if resp.status_code == 201:
            mapping[name] = resp.json()["id"]
            print(f"  Created category '{name}' -> id {resp.json()['id']}")
        elif resp.status_code == 409:
            list_resp = client.get(f"{API_PREFIX}/categories")
            for cat in list_resp.json():
                if cat["name"] == name:
                    mapping[name] = cat["id"]
                    break
        else:
            print(f"  Error creating category '{name}': {resp.status_code}")
    print(f"  Total categories: {len(mapping)}")
    return mapping


def _seed_products(client, headers, products, cat_mapping):
    for i, p in enumerate(products):
        p["is_featured"] = i < FEATURED_COUNT

    created = 0
    skipped = 0
    errors = 0
    for p in products:
        cat_name = p.get("category")
        cat_id = cat_mapping.get(cat_name)
        if cat_id is None:
            errors += 1
            print(f"  Error: unknown category '{cat_name}' for product {p.get('id')}")
            continue
        p["category_id"] = cat_id
        resp = client.post(f"{API_PREFIX}/admin/products", json=p, headers=headers)
        if resp.status_code == 201:
            created += 1
        elif resp.status_code == 409:
            skipped += 1
        else:
            errors += 1
            if errors <= 3:
                print(f"  Error {resp.status_code} for product {p.get('id')}: {resp.text[:100]}")

    print(f"  Products — Created: {created}, Skipped: {skipped}, Errors: {errors}")
    return created


# ── Order & review seeding (direct DB) ──────────────────────────────────

def _create_orders_and_reviews(db, products, users):
    rng = random.Random(RANDOM_SEED)
    order_count = 0
    review_count = 0

    shuffled_products = rng.sample(products, len(products))
    idx = 0

    for user in users:
        for _ in range(5):
            num_items = rng.randint(3, 6)
            items_in_order = shuffled_products[idx : idx + num_items]
            idx += num_items
            if not items_in_order or idx > len(shuffled_products):
                break

            order_subtotal = 0
            item_data = []
            for prod in items_in_order:
                qty = rng.randint(1, 2)
                line_subtotal = round(prod["price"] * qty, 2)
                order_subtotal += line_subtotal
                item_data.append((prod, qty, line_subtotal))

            order_subtotal = round(order_subtotal, 2)
            order = Order(
                user_id=user.id,
                total=order_subtotal,
                subtotal=order_subtotal,
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

            for prod, qty, line_subtotal in item_data:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=prod["id"],
                    product_name=prod["title"],
                    product_price=prod["price"],
                    quantity=qty,
                    subtotal=line_subtotal,
                    thumbnail=prod.get("thumbnail", ""),
                )
                db.add(order_item)

                rating = rng.choices(
                    [1, 2, 3, 4, 5],
                    weights=[1, 2, 4, 5, 3],
                )[0]
                comment = rng.choice(REVIEW_COMMENTS)
                existing = (
                    db.query(Review)
                    .filter(Review.user_id == user.id, Review.product_id == prod["id"])
                    .first()
                )
                if not existing:
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
    print(f"  Created {order_count} orders, {review_count} reviews")


def _recalculate_all_ratings(db):
    """Recalculate product ratings from actual reviews."""
    from app.models.product import Product
    from sqlalchemy import func

    products = db.query(Product).all()
    updated = 0
    for product in products:
        stats = (
            db.query(func.avg(Review.rating), func.count(Review.id))
            .filter(Review.product_id == product.id)
            .first()
        )
        avg_rating = round(float(stats[0] or 0), 2)
        review_count = stats[1] or 0
        if product.rating != avg_rating or product.review_count != review_count:
            product.rating = avg_rating
            product.review_count = review_count
            updated += 1
    db.commit()
    print(f"  Recalculated ratings for {updated} products")


# ── Clear data ──────────────────────────────────────────────────────────

def _clear_all(client, headers):
    db = SessionLocal()
    try:
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(Review).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    resp = client.get(f"{API_PREFIX}/products?limit=1000")
    if resp.status_code == 200:
        for p in resp.json().get("products", []):
            client.delete(f"{API_PREFIX}/admin/products/{p['id']}", headers=headers)

    cat_resp = client.get(f"{API_PREFIX}/categories")
    if cat_resp.status_code == 200:
        for cat in cat_resp.json():
            client.delete(f"{API_PREFIX}/admin/categories/{cat['id']}", headers=headers)

    print("  Cleared existing products, categories, orders, reviews, and order items")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    force = "--force" in sys.argv
    products_only = "--products-only" in sys.argv

    client = TestClient(app)
    db = SessionLocal()

    print("=" * 55)
    print("  Agentic Commerce — Seed Script")
    print("=" * 55)

    # Phase 1: Users
    print("\n── Users ──")
    admin = _get_or_create_admin(db)
    admin_token = create_access_token(subject=admin.id, role=admin.role)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    if not products_only:
        test_users = _create_test_users(db)
    else:
        test_users = []
        print("  Skipping test users (--products-only)")

    # Phase 2: Products
    print("\n── Products ──")
    products = _load_products()
    print(f"  Loaded {len(products)} products from {PRODUCTS_FILE}")

    if force:
        _clear_all(client, admin_headers)

    cat_mapping = _seed_categories(client, admin_headers, products)
    created = _seed_products(client, admin_headers, products, cat_mapping)

    if created == 0:
        print("  No new products created (already seeded)")

    # Phase 3: Orders & reviews
    if not products_only:
        print("\n── Orders & Reviews ──")
        _create_orders_and_reviews(db, products, test_users)
        _recalculate_all_ratings(db)

    # Summary
    print("\n── Summary ──")
    resp = client.get(f"{API_PREFIX}/products?limit=1")
    total_products = resp.json().get("total", 0)

    user_count = db.query(User).count()
    order_count = db.query(Order).count()
    review_count = db.query(Review).count()

    print(f"  Products:   {total_products}")
    print(f"  Users:      {user_count}")
    print(f"  Orders:     {order_count}")
    print(f"  Reviews:    {review_count}")
    print("\n  Test accounts:")
    print(f"    Admin:     admin@admin.com / admin")
    for u in TEST_USERS:
        print(f"    {u['first_name']:8s} {u['email']:25s} / {u['password']}")
    print()
    print("  Done.")

    db.close()


if __name__ == "__main__":
    main()

"""
Seed script: reads products from data/products.json and inserts them into the
database via the POST /api/v1/products endpoint using FastAPI's TestClient.

Usage:
    python scripts/seed_products.py          # seed if DB is empty
    python scripts/seed_products.py --force   # clear and re-seed
"""

import json
import sys
from pathlib import Path

# Ensure the project root is on sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.db.session import SessionLocal
from app.models.user import User

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
API_PREFIX = "/api/v1"


def _get_admin_headers() -> dict:
    db = SessionLocal()
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        admin = User(
            email="seed-admin@example.com",
            hashed_password=get_password_hash("seed-admin-pw"),
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    db.close()
    token = create_access_token(subject=admin.id, role=admin.role)
    return {"Authorization": f"Bearer {token}"}


def load_products() -> list[dict]:
    with open(PRODUCTS_FILE) as f:
        data = json.load(f)
    return data["products"]


def _seed_categories(client, headers, products) -> dict[str, int]:
    """Create all unique categories and return a name->id mapping."""
    names = sorted({p["category"] for p in products})
    mapping = {}
    for name in names:
        resp = client.post(f"{API_PREFIX}/categories", json={"name": name}, headers=headers)
        if resp.status_code == 201:
            mapping[name] = resp.json()["id"]
            print(f"  Created category '{name}' -> id {resp.json()['id']}")
        elif resp.status_code == 409:
            # already exists — fetch it
            list_resp = client.get(f"{API_PREFIX}/categories")
            for cat in list_resp.json():
                if cat["name"] == name:
                    mapping[name] = cat["id"]
                    break
        else:
            print(f"  Error creating category '{name}': {resp.status_code} {resp.text[:120]}")
    print(f"  Total categories: {len(mapping)}")
    return mapping


def seed(force: bool = False) -> None:
    client = TestClient(app)
    headers = _get_admin_headers()
    products = load_products()

    print(f"Loaded {len(products)} products from {PRODUCTS_FILE}")

    if force:
        print("Fetching existing products to clear…")
        resp = client.get(f"{API_PREFIX}/products?limit=1000")
        if resp.status_code == 200:
            existing = resp.json().get("products", [])
            for p in existing:
                client.delete(f"{API_PREFIX}/products/{p['id']}", headers=headers)
            print(f"Deleted {len(existing)} existing products")
        else:
            print("Could not fetch existing products; proceeding anyway")

        print("Fetching existing categories to clear…")
        cat_resp = client.get(f"{API_PREFIX}/categories")
        if cat_resp.status_code == 200:
            for cat in cat_resp.json():
                client.delete(f"{API_PREFIX}/categories/{cat['id']}", headers=headers)
            print(f"Deleted {len(cat_resp.json())} existing categories")

    print("Creating categories…")
    cat_mapping = _seed_categories(client, headers, products)

    created = 0
    skipped = 0
    errors = 0

    for p in products:
        cat_name = p.pop("category", None)
        cat_id = cat_mapping.get(cat_name)
        if cat_id is None:
            errors += 1
            print(f"  Error: unknown category '{cat_name}' for product {p.get('id')}")
            continue
        p["category_id"] = cat_id
        resp = client.post(f"{API_PREFIX}/products", json=p, headers=headers)
        if resp.status_code == 201:
            created += 1
        elif resp.status_code == 409:
            skipped += 1
        else:
            errors += 1
            print(f"  Error {resp.status_code} for product {p.get('id')}: {resp.text[:120]}")

    print(f"\nDone. Created: {created}, Skipped (already exist): {skipped}, Errors: {errors}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed(force=force)

import sys
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

EMAIL = "admin@admin.com"
PASSWORD = "admin"

db = SessionLocal()
try:
    existing = db.query(User).filter(User.email == EMAIL).first()
    if existing:
        print(f"Admin already exists: {existing.email} (role={existing.role})")
    else:
        admin = User(
            email=EMAIL,
            hashed_password=get_password_hash(PASSWORD),
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin created: {EMAIL} / {PASSWORD}")
finally:
    db.close()

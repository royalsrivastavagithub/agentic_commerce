from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, PasswordChange
from app.core.security import (
    get_password_hash,
    generate_verification_token,
    verify_password,
    create_access_token,
)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(email))
        .first()
    )
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    if not user.is_verified:
        return None
    return user


def register_user(db: Session, user_in: UserCreate) -> User:
    existing = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(user_in.email))
        .first()
    )
    if existing:
        raise BadRequestError("Email already registered")

    hashed_password = get_password_hash(user_in.password)
    verification_token = generate_verification_token()

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_verified=False,
        is_active=True,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        date_of_birth=user_in.date_of_birth,
        gender=user_in.gender,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def verify_email(db: Session, token: str) -> User:
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise BadRequestError("Invalid or expired verification token")
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return user


def login_user(db: Session, email: str, password: str) -> dict:
    user = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(email))
        .first()
    )
    if not user:
        raise BadRequestError("Account not found")
    if not verify_password(password, user.hashed_password):
        raise BadRequestError("Invalid credentials")
    if not user.is_active:
        raise BadRequestError("Account is disabled")
    if not user.is_verified:
        raise BadRequestError("Please verify your email before logging in")
    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer", "user": user}


def update_profile(db: Session, user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, pw_in: PasswordChange) -> User:
    if not verify_password(pw_in.current_password, user.hashed_password):
        raise BadRequestError("Current password is incorrect")
    user.hashed_password = get_password_hash(pw_in.new_password)
    user.is_google_account = False
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user: User, new_password: str) -> User:
    user.hashed_password = get_password_hash(new_password)
    user.is_google_account = False
    db.commit()
    db.refresh(user)
    return user


def forgot_password(db: Session, email: str) -> str | None:
    user = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(email))
        .first()
    )
    if not user:
        return None
    token = generate_verification_token()
    user.reset_password_token = token
    user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    return token


def reset_password(db: Session, token: str, new_password: str) -> User:
    user = (
        db.query(User)
        .filter(User.reset_password_token == token)
        .first()
    )
    if not user:
        raise BadRequestError("Invalid or expired reset token")
    if (
        not user.reset_password_token_expires_at
        or datetime.now(timezone.utc) > user.reset_password_token_expires_at
    ):
        user.reset_password_token = None
        user.reset_password_token_expires_at = None
        db.commit()
        raise BadRequestError("Invalid or expired reset token")
    user.hashed_password = get_password_hash(new_password)
    user.reset_password_token = None
    user.reset_password_token_expires_at = None
    db.commit()
    db.refresh(user)
    return user

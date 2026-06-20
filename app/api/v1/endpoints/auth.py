import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.core.security import (
    get_password_hash,
    generate_verification_token,
    verify_password,
    create_access_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(email: str, password: str, db: Session) -> User | None:
    user = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(email))
        .first()
    )
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active or not user.is_verified:
        return None
    return user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(user_in.email))
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user_in.password)
    verification_token = generate_verification_token()

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_verified=False,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    print("\n" + "=" * 60)
    print(f"VERIFICATION TOKEN FOR {new_user.email}:")
    print(f"  {new_user.verification_token}")
    print("=" * 60 + "\n")

    logger.info(
        f"Generated verification token for {new_user.email}: {new_user.verification_token}"
    )

    return new_user


@router.get("/verify-email")
def verify_email(
    token: str = Query(..., description="The verification token printed during signup"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user.is_verified = True
    user.verification_token = None
    db.commit()

    return {
        "message": "Email verified successfully",
        "email": user.email,
        "is_verified": user.is_verified,
    }


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = _authenticate_user(user_in.email, user_in.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

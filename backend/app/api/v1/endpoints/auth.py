import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate, PasswordChange, Token, UserLogin
from app.core.security import (
    get_password_hash,
    generate_verification_token,
    verify_password,
    create_access_token,
)
from app.api.deps import get_current_user

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


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
@limiter.limit("30/minute")
def signup(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
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
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        date_of_birth=user_in.date_of_birth,
        gender=user_in.gender,
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


@router.get("/verify-email", summary="Verify email address with token")
@limiter.limit("30/minute")
def verify_email(
    request: Request,
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


@router.post("/login", response_model=Token, summary="Login with email and password (JSON)")
@limiter.limit("30/minute")
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    user = _authenticate_user(user_in.email, user_in.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/access-token", response_model=Token, summary="Login with email and password (form)")
@limiter.limit("30/minute")
def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse, summary="Get current user profile")
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put("/users/me", response_model=UserResponse, summary="Update current user profile")
def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/users/me/password", response_model=UserResponse, summary="Change current user password")
@limiter.limit("30/minute")
def change_password(
    request: Request,
    pw_in: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(pw_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = get_password_hash(pw_in.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user

import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate, PasswordChange, PasswordSet, Token, TokenWithUser, UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.api.deps import get_current_user
from app.services import user_service
from app.services.google_auth import verify_google_token
from app.core.security import get_password_hash, create_access_token
from app.core.email import send_verification_email, send_password_reset_email

class GoogleLoginRequest(BaseModel):
    id_token: str

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def signup(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    new_user = user_service.register_user(db, user_in)
    token = new_user.verification_token
    logger.info("Generated verification token for %s: %s", new_user.email, token)
    sent = send_verification_email(new_user.email, token)
    if not sent:
        logger.warning("Verification email not sent to %s", new_user.email)
    return new_user


@router.get("/verify-email", summary="Verify email address with token")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def verify_email(
    request: Request,
    token: str = Query(..., description="The verification token printed during signup"),
    db: Session = Depends(get_db),
):
    user = user_service.verify_email(db, token)
    return {
        "message": "Email verified successfully",
        "email": user.email,
        "is_verified": user.is_verified,
    }


@router.post("/google", response_model=TokenWithUser, summary="Login or register with Google Sign-In")
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    info = verify_google_token(body.id_token)
    if not info or not info.get("email"):
        logger.warning("Google token verification failed for token: %s...", body.id_token[:30])
        raise HTTPException(status_code=400, detail="Invalid Google token")

    user = db.query(User).filter(User.email == info["email"]).first()
    if not user:
        user = User(
            email=info["email"],
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            is_verified=True,
            is_active=True,
            is_google_account=True,
            role="user",
            first_name=info.get("first_name") or None,
            last_name=info.get("last_name") or None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=TokenWithUser, summary="Login with email and password (JSON)")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    return user_service.login_user(db, user_in.email, user_in.password)


@router.post("/login/access-token", response_model=TokenWithUser, summary="Login with email and password (form)")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return user_service.login_user(db, form_data.username, form_data.password)


@router.post("/forgot-password", summary="Request password reset email")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    token = user_service.forgot_password(db, body.email)
    if token:
        sent = send_password_reset_email(body.email, token)
        if not sent:
            reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
            logger.info("Password reset URL for %s: %s", body.email, reset_url)
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password", summary="Reset password with token")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    user_service.reset_password(db, body.token, body.new_password)
    return {"message": "Password reset successfully"}


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
    return user_service.update_profile(db, current_user, user_in)


@router.put("/users/me/password", response_model=UserResponse, summary="Change current user password")
@limiter.limit(lambda: f"{settings.RATE_LIMIT}/minute")
def change_password(
    request: Request,
    pw_in: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.change_password(db, current_user, pw_in)


@router.post("/users/me/set-password", response_model=UserResponse, summary="Set password for Google-authenticated users")
def set_password(
    pw_in: PasswordSet,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.set_password(db, current_user, pw_in.new_password)

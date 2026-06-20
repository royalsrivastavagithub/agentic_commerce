import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
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

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user, generate an email verification token, and print it to stdout.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and generate token
    hashed_password = get_password_hash(user_in.password)
    verification_token = generate_verification_token()
    
    # Create user
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_verified=False,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Print the verification token as requested
    print("\n" + "=" * 60)
    print(f"VERIFICATION TOKEN FOR {new_user.email}:")
    print(f"  {new_user.verification_token}")
    print("=" * 60 + "\n")
    
    # Also log it
    logger.info(f"Generated verification token for {new_user.email}: {new_user.verification_token}")
    
    return new_user

@router.get("/verify-email")
def verify_email(
    token: str = Query(..., description="The verification token printed during signup"),
    db: Session = Depends(get_db)
):
    """
    Verify a user's email using the token generated during signup.
    """
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark email as verified and clear the token
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully", "email": user.email, "is_verified": user.is_verified}

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Log in a user with JSON body (email and password), returning a JWT access token.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified. Please verify your email first."
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Log in a user using standard OAuth2 password flow form body, returning a JWT access token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified. Please verify your email first."
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

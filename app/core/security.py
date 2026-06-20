import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt password hash from a plain text password.
    """
    # bcrypt requires bytes
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt password hash.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def generate_verification_token() -> str:
    """
    Generate a cryptographically secure, url-safe token for email verification.
    """
    return secrets.token_urlsafe(32)

def create_access_token(subject: str | int, expires_delta: timedelta = None) -> str:
    """
    Generate a signed JWT access token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str | None:
    """
    Verify and decode a JWT token, returning the subject (e.g. user_id) if valid.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

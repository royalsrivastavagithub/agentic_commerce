from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agentic Commerce"
    
    # SQLite configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./sqlite.db",
        description="SQLAlchemy database connection URL"
    )
    
    # JWT security configuration
    SECRET_KEY: str = Field(
        default="SECRET_KEY_FOR_LOCAL_DEVELOPMENT_PLEASE_CHANGE_IN_PRODUCTION",
        description="JWT signature secret key"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes

    # CORS configuration — list of origins allowed for cross-origin requests.
    # In production, replace with your frontend's deployed URL.
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Google OAuth configuration
    GOOGLE_CLIENT_ID: str = Field(
        default="",
        description="Google OAuth 2.0 Client ID for Sign-In"
    )

    # Razorpay payment gateway configuration
    RAZORPAY_KEY_ID: str = Field(
        default="",
        description="Razorpay API Key ID"
    )
    RAZORPAY_KEY_SECRET: str = Field(
        default="",
        description="Razorpay API Key Secret"
    )
    RAZORPAY_WEBHOOK_SECRET: str = Field(
        default="",
        description="Razorpay webhook signing secret"
    )

    # SMTP email configuration (Gmail App Password recommended for dev)
    SMTP_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname"
    )
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port"
    )
    SMTP_USER: str = Field(
        default="",
        description="SMTP username (full email address)"
    )
    SMTP_PASSWORD: str = Field(
        default="",
        description="SMTP password or App Password"
    )
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend base URL for building verification links"
    )

    RATE_LIMIT: int = Field(
        default=30,
        description="Rate limit per minute for auth endpoints"
    )

settings = Settings()

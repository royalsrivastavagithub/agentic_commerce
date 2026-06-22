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

settings = Settings()

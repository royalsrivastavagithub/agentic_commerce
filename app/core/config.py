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

settings = Settings()

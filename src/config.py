from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_PASSWORD: str
    ENV: str = "development"  # default to development
    FRONTEND_ORIGINS: str
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT argo")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expire time in minutes")
    
    model_config = ConfigDict(
        env_file=".env"
    )
        
settings = Settings()

# Auto url config depending on the environment
def get_database_url() -> str:
    if settings.ENV == "production":
        return settings.DATABASE_URL
    else:
        return f"postgresql://postgres:{settings.DATABASE_PASSWORD}@localhost:5432/crm_dev"
    
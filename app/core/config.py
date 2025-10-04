from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = ""  # Set via environment variable
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = ""  # Set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email Configuration
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""  # Set via environment variable
    EMAIL_PASSWORD: str = ""  # Set via environment variable
    EMAIL_USE_TLS: bool = True
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # AI Configuration
    GEMINI_API_KEY: str = ""  # Set via environment variable
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "localhost",
        "127.0.0.1",
        "*"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
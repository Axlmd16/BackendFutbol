from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # App
    APP_NAME: str = "Backend Futbol API"
    APP_VERSION: str = "1.0.0"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRES: int = 3600
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Email 
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TLS: bool = True

    # Restricciones de correo institucional
    INSTITUTIONAL_EMAIL_DOMAINS: List[str] = []
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"   # <-- forzar UTF-8 al leer .env
        case_sensitive = True

settings = Settings()
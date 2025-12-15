from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    # ================= DATABASE =================
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # ================= APP =================
    APP_NAME: str = "Backend Futbol API"
    APP_VERSION: str = "1.0.0"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    DEBUG: bool = False

    # ================= SECURITY =================
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRES: int = 3600
    REFRESH_EXPIRES: int = 60 * 60 * 24 * 7  # 7 días

    # ================= CORS =================
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ================= EMAIL =================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TLS: bool = True

    # Restricciones de correo institucional
    INSTITUTIONAL_EMAIL_DOMAINS: List[str] = ["@unl.edu.ec"]

    # ================= MICROSERVICE =================
    PERSON_MS_BASE_URL: str = "http://localhost:8096"
    PERSON_MS_ADMIN_EMAIL: str = "admin@admin.com"
    PERSON_MS_ADMIN_PASSWORD: str = "12345678"

    # ================= PROPERTIES =================
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ================= PYDANTIC V2 CONFIG =================
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

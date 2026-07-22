"""
Configuration centralisée via variables d'environnement.
Utilise pydantic-settings pour la validation et le chargement depuis .env.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Toutes les variables de configuration de l'application.
    Les valeurs peuvent être surchargées via le fichier .env ou l'environnement système.
    """

    # --- Identité de l'application ---
    APP_NAME: str = "Analytics Platform API"
    API_VERSION: str = "v1"
    ENV: str = "development"  # development | staging | production

    # --- Sécurité ---
    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_ENABLED: bool = False

    # --- Base de données ---
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/analytics_db"

    # --- Google Analytics 4 ---
    GA4_CREDENTIALS_PATH: str = "credentials/ga4_service_account.json"
    GA4_DEFAULT_PROPERTY_ID: str = ""  # ex: "properties/123456789"

    # --- CORS / Hôtes ---
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    ALLOWED_HOSTS: List[str] = ["*"]

    # --- Redis (optionnel – cache / Celery broker) ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TIMEZONE: str = "Europe/Paris"

    # --- Rétention des données ---
    SNAPSHOT_RETENTION_DAYS: int = 365  # jours de conservation des snapshots GA4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Instance globale importée partout dans l'application
settings = Settings()

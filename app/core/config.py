import sys
import logging

from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str:
    if any("pytest" in arg for arg in sys.argv):
        return ".env.test"
    return ".env.example"


class Settings(BaseSettings):
    # Database settings:
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_POSTGRES: str

    # App settings:
    FAST_API_DEBUG: bool
    ENGINE_DEBUG: bool
    DB_MODELS_UPGRADE: bool
    LOG_LEVEL: str
    APP_BASE_URL: str

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # JWT settings:
    SECRET_KEY_FOR_JWT_AUTH: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email verification settings:
    EMAIL_VERIFICATION_SECRET: str
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SSL_CERT_PATH: str | None = None

    model_config = SettingsConfigDict(env_file=_get_env_file())

    @property
    def engine_options(self) -> dict[str, bool | int]:
        return {
            "echo": self.ENGINE_DEBUG,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=self.LOG_LEVEL,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_psycopg(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_POSTGRES}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()  # type: ignore
templates = Jinja2Templates(directory="app/templates")

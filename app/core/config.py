import sys
import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_POSTGRES: str

    FAST_API_DEBUG: bool
    ENGINE_DEBUG: bool
    DB_MODELS_UPGRADE: bool
    LOG_LEVEL: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    env_file: str = ".env.example"
    if any("pytest" in arg for arg in sys.argv):
        env_file = ".env.test"

    @property
    def engine_options(self) -> dict[str, bool | int]:
        return {
            "echo": self.ENGINE_DEBUG,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,  # секунд ждать свободного коннекта из пула
            "pool_recycle": 1800,  # переоткрывать коннект каждые 30 мин
            "pool_pre_ping": True,  # проверять живость коннекта перед выдачей
        }

    def setup_logging(self, level: str = "INFO") -> None:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    @property
    def DATABASE_URL_psycopg(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        return (
            f"postgresql+asyncpg://"
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

    model_config = SettingsConfigDict(env_file=env_file)


settings = Settings()  # type: ignore

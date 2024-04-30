from enum import Enum

from pydantic import BaseSettings


class StorageType(Enum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"


class PostgresSettings(BaseSettings):
    host: str
    port: int
    db: str
    user: str
    password: str

    class Config:
        env_prefix = "postgres_"


class Settings(BaseSettings):
    storage_type: StorageType = StorageType.SQLITE
    postgres: PostgresSettings = PostgresSettings()


settings = Settings()

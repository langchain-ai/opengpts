import os
import structlog
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = structlog.get_logger(__name__)

class AsyncPostgresCheckpoint:
    _instance: Optional[AsyncPostgresSaver] = None
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> AsyncPostgresSaver:
        if cls._instance is None:
            conninfo = (
                f"postgresql://{os.environ['POSTGRES_USER']}:"
                f"{os.environ['POSTGRES_PASSWORD']}@"
                f"{os.environ['POSTGRES_HOST']}:"
                f"{os.environ['POSTGRES_PORT']}/"
                f"{os.environ['POSTGRES_DB']}"
            )
            _async_pool = AsyncConnectionPool(
                conninfo=conninfo,
                kwargs={"autocommit": True, "prepare_threshold": 0},
            )
            cls._instance = AsyncPostgresSaver(_async_pool)
        return cls._instance

    @classmethod
    async def setup_async(cls) -> None:
        """Asynchronously sets up the checkpoint."""
        cls.get_instance()  # Ensure the instance is created
        if not cls._initialized:
            logger.info("Setting up the checkpoint asynchronously...")
            await cls._instance.setup()
            logger.info("Checkpoint setup complete.")
            cls._initialized = True


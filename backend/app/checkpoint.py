import os
from typing import Any, AsyncIterator, Optional, Sequence

import structlog
from langgraph.checkpoint.base import (
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    RunnableConfig,
)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.postgres.base import BasePostgresSaver
from langgraph.checkpoint.serde.base import SerializerProtocol
from psycopg import AsyncPipeline
from psycopg_pool import AsyncConnectionPool

logger = structlog.get_logger(__name__)


class AsyncPostgresCheckpoint(BasePostgresSaver):
    """A singleton implementation of AsyncPostgresSaver with separate setup."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        pipe: Optional[AsyncPipeline] = None,
        serde: Optional[SerializerProtocol] = None,
    ) -> None:
        if not hasattr(self, "_initialized"):
            super().__init__(serde=serde)
            # Initialize basic attributes
            self.pipe = pipe
            self.serde = serde
            self._initialized = True
            self._setup_complete = False
            self.async_postgres_saver = None

    async def ensure_setup(self) -> None:
        """Ensure the instance is set up before use."""
        if not self._setup_complete:
            await self.setup()
            self._setup_complete = True

    async def setup(self) -> None:
        """Internal setup method."""
        try:
            conninfo = (
                f"postgresql://{os.environ['POSTGRES_USER']}:"
                f"{os.environ['POSTGRES_PASSWORD']}@"
                f"{os.environ['POSTGRES_HOST']}:"
                f"{os.environ['POSTGRES_PORT']}/"
                f"{os.environ['POSTGRES_DB']}"
            )

            pool = AsyncConnectionPool(
                conninfo=conninfo,
                kwargs={"autocommit": True, "prepare_threshold": 0},
                open=False,  # Don't open in constructor
            )
            await pool.open()

            self.async_postgres_saver = AsyncPostgresSaver(
                conn=pool, pipe=self.pipe, serde=self.serde
            )

            # Setup will create/migrate the tables if they don't exist
            await self.async_postgres_saver.setup()

            logger.warning("Checkpoint setup complete.")
        except Exception as e:
            logger.error(f"Failed to set up AsyncPostgresCheckpoint: {e}")
            raise

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints from the database asynchronously."""
        async for checkpoint in self.async_postgres_saver.alist(
            config, filter=filter, before=before, limit=limit
        ):
            yield checkpoint

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple from the database asynchronously."""
        return await self.async_postgres_saver.aget_tuple(config)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to the database asynchronously."""
        return await self.async_postgres_saver.aput(
            config, checkpoint, metadata, new_versions
        )

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Store intermediate writes linked to a checkpoint asynchronously."""
        await self.async_postgres_saver.aput_writes(config, writes, task_id)

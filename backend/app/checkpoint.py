import pickle
from typing import Optional

import asyncpg
from langchain.pydantic_v1 import Field
from langchain.schema.runnable import RunnableConfig
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint

from app.lifespan import get_pg_pool


class PostgresCheckpoint(BaseCheckpointSaver):
    pg_pool: Optional[asyncpg.Pool] = None
    is_setup: bool = Field(False, init=False, repr=False)

    class Config:
        arbitrary_types_allowed = True

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id="thread_id",
                annotation=Optional[str],
                name="Thread ID",
                description=None,
                default=None,
                is_shared=True,
            ),
        ]

    async def setup(self) -> None:
        if self.is_setup:
            return

        if self.pg_pool is None:
            self.pg_pool = get_pg_pool()

        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        thread_id TEXT PRIMARY KEY,
                        checkpoint BYTEA
                    );
                    """
                )
            self.is_setup = True
        except BaseException as e:
            raise e

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        raise NotImplementedError

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        raise NotImplementedError

    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        await self.setup()
        thread_id = config["configurable"]["thread_id"]
        async with self.pg_pool.acquire() as conn:
            if value := await conn.fetchrow(
                "SELECT checkpoint FROM checkpoints WHERE thread_id = $1", thread_id
            ):
                return pickle.loads(value[0])

    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        await self.setup()
        thread_id = config["configurable"]["thread_id"]
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                (
                    "INSERT INTO checkpoints (thread_id, checkpoint) "
                    "VALUES ($1, $2) "
                    "ON CONFLICT (thread_id) "
                    "DO UPDATE SET checkpoint = EXCLUDED.checkpoint;"
                ),
                thread_id,
                pickle.dumps(checkpoint),
            )

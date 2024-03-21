import pickle
from typing import Optional

from langchain.schema.runnable import RunnableConfig
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint

from app.lifespan import get_pg_pool


class PostgresCheckpoint(BaseCheckpointSaver):
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

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        raise NotImplementedError

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        raise NotImplementedError

    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        thread_id = config["configurable"]["thread_id"]
        async with get_pg_pool().acquire() as conn:
            if value := await conn.fetchrow(
                "SELECT checkpoint FROM checkpoints WHERE thread_id = $1", thread_id
            ):
                return pickle.loads(value[0])

    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        thread_id = config["configurable"]["thread_id"]
        async with get_pg_pool().acquire() as conn:
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

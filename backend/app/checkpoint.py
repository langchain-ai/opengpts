import pickle
from datetime import datetime
from typing import AsyncIterator, Optional

from langchain_core.messages import BaseMessage
from langchain_core.runnables import ConfigurableFieldSpec, RunnableConfig
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointAt,
    CheckpointThreadTs,
    CheckpointTuple,
    SerializerProtocol,
)

from app.lifespan import get_pg_pool


def loads(value: bytes) -> Checkpoint:
    loaded: Checkpoint = pickle.loads(value)
    for key, value in loaded["channel_values"].items():
        if isinstance(value, list) and all(isinstance(v, BaseMessage) for v in value):
            loaded["channel_values"][key] = [v.__class__(**v.__dict__) for v in value]
    return loaded


class PostgresCheckpoint(BaseCheckpointSaver):
    def __init__(
        self,
        *,
        serde: Optional[SerializerProtocol] = None,
        at: Optional[CheckpointAt] = None,
    ) -> None:
        super().__init__(serde=serde, at=at)

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
            CheckpointThreadTs,
        ]

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        raise NotImplementedError

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> RunnableConfig:
        raise NotImplementedError

    async def alist(self, config: RunnableConfig) -> AsyncIterator[CheckpointTuple]:
        async with get_pg_pool().acquire() as db, db.transaction():
            thread_id = config["configurable"]["thread_id"]
            async for value in db.cursor(
                "SELECT checkpoint, thread_ts, parent_ts FROM checkpoints WHERE thread_id = $1 ORDER BY thread_ts DESC",
                thread_id,
            ):
                yield CheckpointTuple(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "thread_ts": value[1],
                        }
                    },
                    loads(value[0]),
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "thread_ts": value[2],
                        }
                    }
                    if value[2]
                    else None,
                )

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts")
        async with get_pg_pool().acquire() as conn:
            if thread_ts:
                if value := await conn.fetchrow(
                    "SELECT checkpoint, parent_ts FROM checkpoints WHERE thread_id = $1 AND thread_ts = $2",
                    thread_id,
                    datetime.fromisoformat(thread_ts),
                ):
                    return CheckpointTuple(
                        config,
                        loads(value[0]),
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "thread_ts": value[1],
                            }
                        }
                        if value[1]
                        else None,
                    )
            else:
                if value := await conn.fetchrow(
                    "SELECT checkpoint, thread_ts, parent_ts FROM checkpoints WHERE thread_id = $1 ORDER BY thread_ts DESC LIMIT 1",
                    thread_id,
                ):
                    return CheckpointTuple(
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "thread_ts": value[1],
                            }
                        },
                        loads(value[0]),
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "thread_ts": value[2],
                            }
                        }
                        if value[2]
                        else None,
                    )

    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        thread_id = config["configurable"]["thread_id"]
        async with get_pg_pool().acquire() as conn:
            await conn.execute(
                """
                INSERT INTO checkpoints (thread_id, thread_ts, parent_ts, checkpoint)
                VALUES ($1, $2, $3, $4) 
                ON CONFLICT (thread_id, thread_ts) 
                DO UPDATE SET checkpoint = EXCLUDED.checkpoint;""",
                thread_id,
                datetime.fromisoformat(checkpoint["ts"]),
                datetime.fromisoformat(checkpoint.get("parent_ts"))
                if checkpoint.get("parent_ts")
                else None,
                pickle.dumps(checkpoint),
            )
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            }
        }

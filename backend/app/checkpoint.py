import pickle
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, Optional

from langchain_core.messages import BaseMessage
from langchain_core.runnables import ConfigurableFieldSpec, RunnableConfig
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointThreadTs, CheckpointTuple


@contextmanager
def _connect():
    conn = sqlite3.connect("opengpts.db")
    conn.row_factory = sqlite3.Row  # Enable dictionary access to row items.
    try:
        yield conn
    finally:
        conn.close()


def loads(value: bytes) -> Checkpoint:
    loaded: Checkpoint = pickle.loads(value)
    for key, value in loaded["channel_values"].items():
        if isinstance(value, list) and all(isinstance(v, BaseMessage) for v in value):
            loaded["channel_values"][key] = [v.__class__(**v.__dict__) for v in value]
    return loaded


class SQLiteCheckpoint(BaseCheckpointSaver):
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
            CheckpointThreadTs,
        ]

    # Adapting the get method
    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        # Implementation adapted for SQLite
        raise NotImplementedError

    # Adapting the put method
    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> RunnableConfig:
        # Implementation adapted for SQLite
        raise NotImplementedError

    # Adapting the alist method
    def alist(self, config: RunnableConfig) -> Iterator[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        with _connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checkpoint, thread_ts, parent_ts FROM checkpoints WHERE thread_id = ? ORDER BY thread_ts DESC",
                (thread_id,),
            )
            for value in cursor.fetchall():
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

    # Adapting the aget_tuple method
    def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts")
        with _connect() as conn:
            cursor = conn.cursor()
            if thread_ts:
                cursor.execute(
                    "SELECT checkpoint, parent_ts FROM checkpoints WHERE thread_id = ? AND thread_ts = ?",
                    (thread_id, datetime.fromisoformat(thread_ts)),
                )
            else:
                cursor.execute(
                    "SELECT checkpoint, thread_ts, parent_ts FROM checkpoints WHERE thread_id = ? ORDER BY thread_ts DESC LIMIT 1",
                    (thread_id,),
                )
            value = cursor.fetchone()
            if value:
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
            return None

    # Adapting the aput method
    def aput(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        thread_id = config["configurable"]["thread_id"]
        with _connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO checkpoints (thread_id, thread_ts, parent_ts, checkpoint)
                VALUES (?, ?, ?, ?) 
                ON CONFLICT (thread_id, thread_ts) 
                DO UPDATE SET checkpoint = EXCLUDED.checkpoint;
                """,
                (
                    thread_id,
                    datetime.fromisoformat(checkpoint["ts"]),
                    datetime.fromisoformat(checkpoint.get("parent_ts", "")),
                    pickle.dumps(checkpoint),
                ),
            )
            conn.commit()
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            }
        }

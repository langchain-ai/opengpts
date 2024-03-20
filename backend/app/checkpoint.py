import pickle
from typing import Any, Optional

from langchain.pydantic_v1 import Field
from langchain.schema.runnable import RunnableConfig
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint, empty_checkpoint
from redis.client import Redis as RedisType

from app.redis import get_redis_client


def checkpoint_key(user_id: str, thread_id: str):
    return f"opengpts:{user_id}:thread:{thread_id}:checkpoint"


def _dump(mapping: dict[str, Any]) -> dict:
    return {k: pickle.dumps(v) if v is not None else None for k, v in mapping.items()}


def _load(mapping: dict[bytes, bytes]) -> dict:
    return {
        k.decode(): pickle.loads(v) if v is not None else None
        for k, v in mapping.items()
    }


class RedisCheckpoint(BaseCheckpointSaver):
    client: RedisType = Field(default_factory=get_redis_client)

    class Config:
        arbitrary_types_allowed = True

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        # Although the annotations are Optional[str], both fields are actually
        # required to create a valid checkpoint key.
        return [
            ConfigurableFieldSpec(
                id="user_id",
                annotation=Optional[str],
                name="User ID",
                description=None,
                default=None,
                is_shared=True,
            ),
            ConfigurableFieldSpec(
                id="thread_id",
                annotation=Optional[str],
                name="Thread ID",
                description=None,
                default=None,
                is_shared=True,
            ),
        ]

    def _hash_key(self, config: RunnableConfig) -> str:
        return checkpoint_key(
            config["configurable"]["user_id"], config["configurable"]["thread_id"]
        )

    def get(self, config: RunnableConfig) -> Checkpoint | None:
        value = _load(self.client.hgetall(self._hash_key(config)))
        if value.get("v") == 1:
            # langgraph version 1
            return value
        elif value.get("__pregel_version") == 1:
            # permchain version 1
            value.pop("__pregel_version")
            value.pop("__pregel_ts")
            checkpoint = empty_checkpoint()
            if value.get("messages"):
                checkpoint["channel_values"] = {"__root__": value["messages"][1]}
            else:
                checkpoint["channel_values"] = {}
            for key in checkpoint["channel_values"]:
                checkpoint["channel_versions"][key] = 1
            return checkpoint
        else:
            # unknown version
            return None

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        return self.client.hmset(self._hash_key(config), _dump(checkpoint))

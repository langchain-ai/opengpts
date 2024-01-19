import os
import pickle
from functools import partial
from typing import Any

from langchain.pydantic_v1 import Field
from langchain.schema.runnable import RunnableConfig
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langchain.utilities.redis import get_client
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint, empty_checkpoint
from redis.client import Redis as RedisType


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
    client: RedisType = Field(
        default_factory=partial(get_client, os.environ.get("REDIS_URL"))
    )

    class Config:
        arbitrary_types_allowed = True

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id="user_id",
                annotation=str,
                name="User ID",
                description=None,
                default=None,
                is_shared=True,
            ),
            ConfigurableFieldSpec(
                id="thread_id",
                annotation=str,
                name="Thread ID",
                description=None,
                default="",
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
            checkpoint["channel_values"] = value
            for key in value:
                checkpoint["channel_versions"][key] = 1
            return checkpoint
        else:
            # unknown version
            return None

    def put(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        return self.client.hmset(self._hash_key(config), _dump(checkpoint))

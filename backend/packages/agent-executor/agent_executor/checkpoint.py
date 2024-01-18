import os
import pickle
from functools import partial
from typing import Any, Mapping

from langchain.pydantic_v1 import Field
from langchain.schema.runnable import RunnableConfig
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langchain.utilities.redis import get_client
from permchain.checkpoint.base import BaseCheckpointAdapter
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


class RedisCheckpoint(BaseCheckpointAdapter):
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

    def get(self, config: RunnableConfig) -> Mapping[str, Any] | None:
        return _load(self.client.hgetall(self._hash_key(config)))

    def put(self, config: RunnableConfig, checkpoint: Mapping[str, Any]) -> None:
        return self.client.hmset(self._hash_key(config), _dump(checkpoint))

import asyncio
import json
import logging
import os
import pickle
import struct
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterator, Optional

import asyncpg
import orjson
from langchain.utilities.redis import get_client
from langchain_core.runnables import ConfigurableFieldSpec, RunnableConfig
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import (
    Checkpoint,
    empty_checkpoint,
)
from redis.client import Redis as RedisType

from app.checkpoint import PostgresCheckpoint
from app.lifespan import get_pg_pool, lifespan
from app.server import app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

redis_client: RedisType = get_client(os.environ["REDIS_URL"], socket_keepalive=True)

thread_hash_keys = ["assistant_id", "name", "updated_at"]
assistant_hash_keys = ["name", "config", "updated_at", "public"]
embedding_hash_keys = ["namespace", "source", "content_vector", "title", "content"]
public_user_id = "eef39817-c173-4eb6-8be4-f77cf37054fb"


def keys(match: str) -> Iterator[str]:
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match=match, count=100)
        for key in keys:
            yield key.decode("utf-8")
        if cursor == 0:
            break


def load(keys: list[str], values: list[bytes]) -> dict:
    return {k: orjson.loads(v) if v is not None else None for k, v in zip(keys, values)}


class RedisCheckpoint(BaseCheckpointSaver):
    class Config:
        arbitrary_types_allowed = True

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
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

    def _dump(self, mapping: dict[str, Any]) -> dict:
        return {
            k: pickle.dumps(v) if v is not None else None for k, v in mapping.items()
        }

    def _load(self, mapping: dict[bytes, bytes]) -> dict:
        return {
            k.decode(): pickle.loads(v) if v is not None else None
            for k, v in mapping.items()
        }

    def _hash_key(self, config: RunnableConfig) -> str:
        user_id = config["configurable"]["user_id"]
        thread_id = config["configurable"]["thread_id"]
        return f"opengpts:{user_id}:thread:{thread_id}:checkpoint"

    def get(self, config: RunnableConfig) -> Checkpoint | None:
        value = self._load(redis_client.hgetall(self._hash_key(config)))
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
        return redis_client.hmset(self._hash_key(config), self._dump(checkpoint))


async def migrate_assistants(conn: asyncpg.Connection) -> None:
    logger.info("Migrating assistants.")

    for key in keys("opengpts:*:assistant:*"):
        parts = key.split(":")
        user_id, assistant_id = parts[1], parts[3]
        if user_id == public_user_id:
            continue

        values = redis_client.hmget(key, *assistant_hash_keys)
        assistant = load(assistant_hash_keys, values) if any(values) else None
        if assistant is not None:
            await conn.execute(
                (
                    "INSERT INTO assistant (assistant_id, user_id, name, config, updated_at, public) "
                    "VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (assistant_id) DO UPDATE SET "
                    "user_id = EXCLUDED.user_id, name = EXCLUDED.name, config = EXCLUDED.config, "
                    "updated_at = EXCLUDED.updated_at, public = EXCLUDED.public;"
                ),
                assistant_id,
                user_id,
                assistant["name"],
                assistant["config"],
                datetime.fromisoformat(assistant["updated_at"]),
                assistant["public"],
            )
            logger.info(f"Migrated assistant {assistant_id} for user {user_id}.")


async def migrate_threads(conn: asyncpg.Connection) -> None:
    logger.info("Migrating threads.")

    for key in keys("opengpts:*:thread:*"):
        if key.endswith(":checkpoint"):
            continue

        parts = key.split(":")
        user_id, thread_id = parts[1], parts[3]

        values = redis_client.hmget(key, *thread_hash_keys)
        thread = load(thread_hash_keys, values) if any(values) else None
        if thread is not None:
            await conn.execute(
                (
                    "INSERT INTO thread (thread_id, assistant_id, user_id, name, updated_at) "
                    "VALUES ($1, $2, $3, $4, $5) ON CONFLICT (thread_id) DO UPDATE SET "
                    "assistant_id = EXCLUDED.assistant_id, user_id = EXCLUDED.user_id, "
                    "name = EXCLUDED.name, updated_at = EXCLUDED.updated_at;"
                ),
                thread_id,
                thread["assistant_id"],
                user_id,
                thread["name"],
                datetime.fromisoformat(thread["updated_at"]),
            )
            logger.info(f"Migrated thread {thread_id} for user {user_id}.")


async def migrate_checkpoints() -> None:
    logger.info("Migrating checkpoints.")

    redis_checkpoint = RedisCheckpoint()
    postgres_checkpoint = PostgresCheckpoint()

    for key in keys("opengpts:*:thread:*:checkpoint"):
        parts = key.split(":")
        user_id, thread_id = parts[1], parts[3]
        config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}
        checkpoint = redis_checkpoint.get(config)
        if checkpoint:
            if checkpoint.get("channel_values", {}).get("__root__"):
                checkpoint["channel_values"]["__root__"] = [
                    msg.__class__(**msg.__dict__)
                    for msg in checkpoint["channel_values"]["__root__"]
                ]
            await postgres_checkpoint.aput(config, checkpoint)
            logger.info(
                f"Migrated checkpoint for thread {thread_id} for user {user_id}."
            )


async def migrate_embeddings(conn: asyncpg.Connection) -> None:
    logger.info("Migrating embeddings.")

    custom_ids = defaultdict(lambda: str(uuid.uuid4()))

    def _get_custom_id(doc: dict) -> str:
        """custom_id is unique for each namespace."""
        return custom_ids[doc["namespace"]]

    def _redis_to_postgres_vector(binary_data: bytes) -> list[float]:
        """Deserialize binary data to a list of floats."""
        assert len(binary_data) == 4 * 1536, "Invalid binary data length."
        format_str = "<" + "1536f"
        return list(struct.unpack(format_str, binary_data))

    def _load_doc(values: list) -> Optional[str]:
        doc = {}
        for k, v in zip(embedding_hash_keys, values):
            if k == "content_vector":
                doc[k] = _redis_to_postgres_vector(v)
            else:
                doc[k] = v.decode() if v is not None else None
        return doc

    def _get_cmetadata(doc: dict) -> str:
        return json.dumps(
            {
                "source": doc["source"] if doc["source"] else None,
                "namespace": doc["namespace"],
                "title": doc["title"],
            }
        )

    def _get_document(doc: dict) -> str:
        """Sanitize the content by replacing null bytes."""
        return doc["content"].replace("\x00", "x")

    def _get_embedding(doc: dict) -> str:
        return str(doc["content_vector"])

    default_collection = await conn.fetchrow(
        "SELECT uuid FROM langchain_pg_collection WHERE name = $1;", "langchain"
    )
    assert (
        default_collection is not None
    ), "Default collection not found in the database."

    for key in keys("doc:*"):
        values = redis_client.hmget(key, *embedding_hash_keys)
        doc = _load_doc(values)
        await conn.execute(
            (
                "INSERT INTO langchain_pg_embedding (document, collection_id, cmetadata, custom_id, embedding, uuid) "
                "VALUES ($1, $2, $3, $4, $5, $6);"
            ),
            _get_document(doc),
            default_collection["uuid"],
            _get_cmetadata(doc),
            _get_custom_id(doc),
            _get_embedding(doc),
            str(uuid.uuid4()),
        )
        logger.info(f"Migrated embedding for namespace {doc['namespace']}.")


async def migrate_data():
    logger.info("Starting to migrate data from Redis to Postgres.")
    async with get_pg_pool().acquire() as conn, conn.transaction():
        await migrate_assistants(conn)
        await migrate_threads(conn)
        await migrate_checkpoints()
        await migrate_embeddings(conn)
    logger.info("Data was migrated successfully.")


async def main():
    async with lifespan(app):
        await migrate_data()


if __name__ == "__main__":
    asyncio.run(main())

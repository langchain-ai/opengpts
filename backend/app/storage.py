import os
from datetime import datetime
from typing import List, Sequence

import orjson
from agent_executor.checkpoint import RedisCheckpoint
from langchain.schema.messages import AnyMessage
from langchain.utilities.redis import get_client
from permchain.channels import Topic
from permchain.channels.base import ChannelsManager, create_checkpoint
from redis.client import Redis as RedisType

from app.schema import Assistant, AssistantWithoutUserId, Thread, ThreadWithoutUserId


def assistants_list_key(user_id: str) -> str:
    return f"opengpts:{user_id}:assistants"


def assistant_key(user_id: str, assistant_id: str) -> str:
    return f"opengpts:{user_id}:assistant:{assistant_id}"


def threads_list_key(user_id: str) -> str:
    return f"opengpts:{user_id}:threads"


def thread_key(user_id: str, thread_id: str) -> str:
    return f"opengpts:{user_id}:thread:{thread_id}"


assistant_hash_keys = ["assistant_id", "name", "config", "updated_at", "public"]
thread_hash_keys = ["assistant_id", "thread_id", "name", "updated_at"]
public_user_id = "eef39817-c173-4eb6-8be4-f77cf37054fb"


def _dump(map: dict) -> dict:
    return {k: orjson.dumps(v) if v is not None else None for k, v in map.items()}


def load(keys: list[str], values: list[bytes]) -> dict:
    return {k: orjson.loads(v) if v is not None else None for k, v in zip(keys, values)}


def _get_redis_client() -> RedisType:
    """Get a Redis client."""
    url = os.environ.get("REDIS_URL")
    if not url:
        raise ValueError("REDIS_URL not set")
    return get_client(url)


def list_assistants(user_id: str) -> List[Assistant]:
    """List all assistants for the current user."""
    client = _get_redis_client()
    ids = [orjson.loads(id) for id in client.smembers(assistants_list_key(user_id))]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_key(user_id, id), *assistant_hash_keys)
        assistants = pipe.execute()
    return [load(assistant_hash_keys, values) for values in assistants]


def get_assistant(user_id: str, assistant_id: str) -> Assistant | None:
    """Get an assistant by ID."""
    client = _get_redis_client()
    values = client.hmget(assistant_key(user_id, assistant_id), *assistant_hash_keys)
    return load(assistant_hash_keys, values) if any(values) else None


def list_public_assistants(
    assistant_ids: Sequence[str]
) -> List[AssistantWithoutUserId]:
    """List all the public assistants."""
    if not assistant_ids:
        return []
    client = _get_redis_client()
    ids = [
        id
        for id, is_public in zip(
            assistant_ids,
            client.smismember(
                assistants_list_key(public_user_id),
                [orjson.dumps(id) for id in assistant_ids],
            ),
        )
        if is_public
    ]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_key(public_user_id, id), *assistant_hash_keys)
        assistants = pipe.execute()
    return [load(assistant_hash_keys, values) for values in assistants]


def put_assistant(
    user_id: str, assistant_id: str, *, name: str, config: dict, public: bool = False
) -> Assistant:
    """Modify an assistant.

    Args:
        user_id: The user ID.
        assistant_id: The assistant ID.
        name: The assistant name.
        config: The assistant config.
        public: Whether the assistant is public.

    Returns:
        return the assistant model if no exception is raised.
    """
    saved: Assistant = {
        "user_id": user_id,  # TODO(Nuno): Could we remove this?
        "assistant_id": assistant_id,  # TODO(Nuno): remove this?
        "name": name,
        "config": config,
        "updated_at": datetime.utcnow(),
        "public": public,
    }
    client = _get_redis_client()
    with client.pipeline() as pipe:
        pipe.sadd(assistants_list_key(user_id), orjson.dumps(assistant_id))
        pipe.hset(assistant_key(user_id, assistant_id), mapping=_dump(saved))
        if public:
            pipe.sadd(assistants_list_key(public_user_id), orjson.dumps(assistant_id))
            pipe.hset(assistant_key(public_user_id, assistant_id), mapping=_dump(saved))
        pipe.execute()
    return saved


def list_threads(user_id: str) -> List[ThreadWithoutUserId]:
    """List all threads for the current user."""
    client = _get_redis_client()
    ids = [orjson.loads(id) for id in client.smembers(threads_list_key(user_id))]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(thread_key(user_id, id), *thread_hash_keys)
        threads = pipe.execute()
    return [load(thread_hash_keys, values) for values in threads]


def get_thread(user_id: str, thread_id: str) -> Thread | None:
    """Get a thread by ID."""
    client = _get_redis_client()
    values = client.hmget(thread_key(user_id, thread_id), *thread_hash_keys)
    return load(thread_hash_keys, values) if any(values) else None


def get_thread_messages(user_id: str, thread_id: str):
    """Get all messages for a thread."""
    client = RedisCheckpoint()
    checkpoint = client.get(
        {"configurable": {"user_id": user_id, "thread_id": thread_id}}
    )
    # TODO replace hardcoded messages channel with
    # channel extracted from agent
    with ChannelsManager(
        {"messages": Topic(AnyMessage, accumulate=True)}, checkpoint
    ) as channels:
        return {k: v.get() for k, v in channels.items()}


def post_thread_messages(user_id: str, thread_id: str, messages: Sequence[AnyMessage]):
    """Add messages to a thread."""
    client = RedisCheckpoint()
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}
    checkpoint = client.get(config)
    # TODO replace hardcoded messages channel with
    # channel extracted from agent
    with ChannelsManager(
        {"messages": Topic(AnyMessage, accumulate=True)}, checkpoint
    ) as channels:
        channels["messages"].update(messages)
        checkpoint = {
            k: v for k, v in create_checkpoint(channels).items() if k == "messages"
        }
        client.put(config, checkpoint)


def put_thread(user_id: str, thread_id: str, *, assistant_id: str, name: str) -> Thread:
    """Modify a thread."""
    saved: Thread = {
        "user_id": user_id,  # TODO(Nuno): Could we remove this?
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "name": name,
        "updated_at": datetime.utcnow(),
    }
    client = _get_redis_client()
    with client.pipeline() as pipe:
        pipe.sadd(threads_list_key(user_id), orjson.dumps(thread_id))
        pipe.hset(thread_key(user_id, thread_id), mapping=_dump(saved))
        pipe.execute()
    return saved


if __name__ == "__main__":
    print(list_assistants("133"))
    print(list_threads("123"))
    put_assistant("123", "i-am-a-test", name="Test Agent", config={"tags": ["hello"]})
    put_thread("123", "i-am-a-test", "test1", name="Test Thread")

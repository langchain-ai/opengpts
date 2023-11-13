import os
from datetime import datetime

import orjson
from langchain.schema.messages import messages_from_dict
from langchain.utilities.redis import get_client
from redis.client import Redis as RedisType


def assistants_list_key(user_id: str):
    return f"opengpts:{user_id}:assistants"


def assistant_key(user_id: str, assistant_id: str):
    return f"opengpts:{user_id}:assistant:{assistant_id}"


def threads_list_key(user_id: str):
    return f"opengpts:{user_id}:threads"


def thread_key(user_id: str, thread_id: str):
    return f"opengpts:{user_id}:thread:{thread_id}"


def thread_messages_key(user_id: str, thread_id: str):
    # Needs to match key used by RedisChatMessageHistory
    # TODO we probably want to align this with the others
    return f"message_store:{user_id}:{thread_id}"


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


def list_assistants(user_id: str):
    client = _get_redis_client()
    ids = [orjson.loads(id) for id in client.smembers(assistants_list_key(user_id))]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_key(user_id, id), *assistant_hash_keys)
        assistants = pipe.execute()
    return [load(assistant_hash_keys, values) for values in assistants]


def list_public_assistants(assistant_ids: list[str]):
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
):
    saved = {
        "user_id": user_id,
        "assistant_id": assistant_id,
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


def list_threads(user_id: str):
    client = _get_redis_client()
    ids = [orjson.loads(id) for id in client.smembers(threads_list_key(user_id))]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(thread_key(user_id, id), *thread_hash_keys)
        threads = pipe.execute()
    return [load(thread_hash_keys, values) for values in threads]


def get_thread_messages(user_id: str, thread_id: str):
    client = _get_redis_client()
    messages = client.lrange(thread_messages_key(user_id, thread_id), 0, -1)
    return {
        "messages": [
            m.dict()
            for m in messages_from_dict([orjson.loads(m) for m in messages[::-1]])
        ],
    }


def put_thread(user_id: str, thread_id: str, *, assistant_id: str, name: str):
    saved = {
        "user_id": user_id,
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

import os
from datetime import datetime

import orjson
from langchain.schema.messages import messages_from_dict
from langchain.utilities.redis import get_client


def assistants_list_key():
    return "opengpts:assistants"


def assistant_key(assistant_id: str):
    return f"opengpts:assistant:{assistant_id}"


def threads_list_key():
    return "opengpts:threads"


def thread_key(thread_id: str):
    return f"opengpts:thread:{thread_id}"


def thread_messages_key(thread_id: str):
    # Needs to match key used by RedisChatMessageHistory
    # TODO we probably want to align this with the others
    return f"message_store:{thread_id}"


assistant_hash_keys = ["assistant_id", "name", "config", "updated_at"]
thread_hash_keys = ["assistant_id", "thread_id", "name", "updated_at"]


def dump(map: dict) -> dict:
    return {k: orjson.dumps(v) if v is not None else None for k, v in map.items()}


def load(keys: list[str], values: list[bytes]) -> dict:
    return {k: orjson.loads(v) if v is not None else None for k, v in zip(keys, values)}


def list_assistants():
    client = get_client(os.environ.get("REDIS_URL"))
    ids = [orjson.loads(id) for id in client.smembers(assistants_list_key())]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_key(id), *assistant_hash_keys)
        assistants = pipe.execute()
    return [load(assistant_hash_keys, values) for values in assistants]


def put_assistant(assistant_id: str, *, name: str, config: dict):
    saved = {
        "assistant_id": assistant_id,
        "name": name,
        "config": config,
        "updated_at": datetime.utcnow(),
    }
    client = get_client(os.environ.get("REDIS_URL"))
    with client.pipeline() as pipe:
        pipe.sadd(assistants_list_key(), orjson.dumps(assistant_id))
        pipe.hset(assistant_key(assistant_id), mapping=dump(saved))
        pipe.execute()
    return saved


def list_threads():
    client = get_client(os.environ.get("REDIS_URL"))
    ids = [orjson.loads(id) for id in client.smembers(threads_list_key())]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(thread_key(id), *thread_hash_keys)
        threads = pipe.execute()
    return [load(thread_hash_keys, values) for values in threads]


def get_thread_messages(thread_id: str):
    client = get_client(os.environ.get("REDIS_URL"))
    messages = client.lrange(thread_messages_key(thread_id), 0, -1)
    return {
        "messages": [
            m.dict()
            for m in messages_from_dict([orjson.loads(m) for m in messages[::-1]])
        ],
    }


def put_thread(thread_id: str, *, assistant_id: str, name: str):
    saved = {
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "name": name,
        "updated_at": datetime.utcnow(),
    }
    client = get_client(os.environ.get("REDIS_URL"))
    with client.pipeline() as pipe:
        pipe.sadd(threads_list_key(), orjson.dumps(thread_id))
        pipe.hset(thread_key(thread_id), mapping=dump(saved))
        pipe.execute()
    return saved


if __name__ == "__main__":
    print(list_assistants())
    print(list_threads("i-am-a-test"))
    put_assistant("i-am-a-test", name="Test Agent", config={"tags": ["hello"]})
    put_thread("i-am-a-test", "test1", name="Test Thread")

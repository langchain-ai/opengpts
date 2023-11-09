from datetime import datetime
import os

import orjson
from langchain.utilities.redis import get_client


def assistants_list_key():
    return "opengpts:assistants"


def assistant_key(assistant_id: str):
    return f"opengpts:assistant:{assistant_id}"


def assistant_threads_list_key(assistant_id: str):
    return f"opengpts:assistant:{assistant_id}:threads"


def assistant_thread_key(assistant_id: str, thread_id: str):
    return f"opengpts:assistant:{assistant_id}:thread:{thread_id}"


assistant_hash_keys = ["name", "config", "updated_at"]
thread_hash_keys = ["name", "updated_at"]


def list_assistants():
    client = get_client(os.environ.get("REDIS_URL"))
    ids = [orjson.loads(id) for id in client.smembers(assistants_list_key())]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_key(id), *assistant_hash_keys)
        assistants = pipe.execute()
    return [
        {
            "id": id,
            **{
                key: orjson.loads(value) if value else None
                for key, value in zip(assistant_hash_keys, values)
            },
        }
        for id, values in zip(ids, assistants)
    ]


def put_assistant(assistant_id: str, *, name: str, config: dict):
    client = get_client(os.environ.get("REDIS_URL"))
    with client.pipeline() as pipe:
        pipe.sadd(assistants_list_key(), orjson.dumps(assistant_id))
        pipe.hset(
            assistant_key(assistant_id),
            mapping={
                "name": orjson.dumps(name),
                "config": orjson.dumps(config),
                "updated_at": orjson.dumps(datetime.utcnow()),
            },
        )
        pipe.execute()


def list_threads(assistant_id: str):
    client = get_client(os.environ.get("REDIS_URL"))
    ids = [
        orjson.loads(id)
        for id in client.smembers(assistant_threads_list_key(assistant_id))
    ]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_thread_key(assistant_id, id), *thread_hash_keys)
        threads = pipe.execute()
    return [
        {
            "id": id,
            **{
                key: orjson.loads(value) if value else None
                for key, value in zip(thread_hash_keys, values)
            },
        }
        for id, values in zip(ids, threads)
    ]


def put_thread(assistant_id: str, thread_id: str, *, name: str):
    client = get_client(os.environ.get("REDIS_URL"))
    with client.pipeline() as pipe:
        pipe.sadd(assistant_threads_list_key(assistant_id), orjson.dumps(thread_id))
        pipe.hset(
            assistant_thread_key(assistant_id, thread_id),
            mapping={
                "name": orjson.dumps(name),
                "updated_at": orjson.dumps(datetime.utcnow()),
            },
        )
        pipe.execute()


if __name__ == "__main__":
    print(list_assistants())
    print(list_threads("i-am-a-test"))
    put_assistant("i-am-a-test", name="Test Agent", config={"tags": ["hello"]})
    put_thread("i-am-a-test", "i-am-a-test-thread", name="Test Thread")

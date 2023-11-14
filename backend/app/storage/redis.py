import os
import orjson
from typing import List
from datetime import datetime
from redis.client import Redis as RedisType
from langchain.schema.messages import messages_from_dict
from langchain.utilities.redis import get_client

from .base import BaseStorage


class RedisStorage(BaseStorage):
    """Redis storage for backend"""

    assistant_hash_keys: List[str] = [
        "assistant_id",
        "name",
        "config",
        "updated_at",
        "public",
    ]
    thread_hash_keys: List[str] = ["assistant_id", "thread_id", "name", "updated_at"]
    public_user_id: str = "eef39817-c173-4eb6-8be4-f77cf37054fb"

    def _get_redis_client(self) -> RedisType:
        """Get a Redis client."""
        url = os.environ.get("REDIS_URL")
        if not url:
            raise ValueError("REDIS_URL not set")
        return get_client(url)

    def list_assistants(self, user_id: str):
        client = self._get_redis_client()
        ids = [
            orjson.loads(id)
            for id in client.smembers(self.assistants_list_key(user_id))
        ]
        with client.pipeline() as pipe:
            for id in ids:
                pipe.hmget(self.assistant_key(user_id, id), *self.assistant_hash_keys)
            assistants = pipe.execute()
        return [self.load(self.assistant_hash_keys, values) for values in assistants]

    def list_public_assistants(self, assistant_ids: list[str]):
        if not assistant_ids:
            return []
        client = self._get_redis_client()
        ids = [
            id
            for id, is_public in zip(
                assistant_ids,
                client.smismember(
                    self.assistants_list_key(self.public_user_id),
                    [orjson.dumps(id) for id in assistant_ids],
                ),
            )
            if is_public
        ]
        with client.pipeline() as pipe:
            for id in ids:
                pipe.hmget(
                    self.assistant_key(self.public_user_id, id),
                    *self.assistant_hash_keys
                )
            assistants = pipe.execute()
        return [self.load(self.assistant_hash_keys, values) for values in assistants]

    def put_assistant(
        self,
        user_id: str,
        assistant_id: str,
        *,
        name: str,
        config: dict,
        public: bool = False
    ):
        saved = {
            "user_id": user_id,
            "assistant_id": assistant_id,
            "name": name,
            "config": config,
            "updated_at": datetime.utcnow(),
            "public": public,
        }
        client = self._get_redis_client()
        with client.pipeline() as pipe:
            pipe.sadd(self.assistants_list_key(user_id), orjson.dumps(assistant_id))
            pipe.hset(
                self.assistant_key(user_id, assistant_id), mapping=self._dump(saved)
            )
            if public:
                pipe.sadd(
                    self.assistants_list_key(self.public_user_id),
                    orjson.dumps(assistant_id),
                )
                pipe.hset(
                    self.assistant_key(self.public_user_id, assistant_id),
                    mapping=self._dump(saved),
                )
            pipe.execute()
        return saved

    def list_threads(self, user_id: str):
        client = self._get_redis_client()
        ids = [
            orjson.loads(id) for id in client.smembers(self.threads_list_key(user_id))
        ]
        with client.pipeline() as pipe:
            for id in ids:
                pipe.hmget(self.thread_key(user_id, id), *self.thread_hash_keys)
            threads = pipe.execute()
        return [self.load(self.thread_hash_keys, values) for values in threads]

    def get_thread_messages(self, user_id: str, thread_id: str):
        client = self._get_redis_client()
        messages = client.lrange(self.thread_messages_key(user_id, thread_id), 0, -1)
        return {
            "messages": [
                m.dict()
                for m in messages_from_dict([orjson.loads(m) for m in messages[::-1]])
            ],
        }

    def put_thread(self, user_id: str, thread_id: str, *, assistant_id: str, name: str):
        saved = {
            "user_id": user_id,
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "name": name,
            "updated_at": datetime.utcnow(),
        }
        client = self._get_redis_client()
        with client.pipeline() as pipe:
            pipe.sadd(self.threads_list_key(user_id), orjson.dumps(thread_id))
            pipe.hset(self.thread_key(user_id, thread_id), mapping=self._dump(saved))
            pipe.execute()
        return saved

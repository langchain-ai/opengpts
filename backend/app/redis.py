import os

from langchain.utilities.redis import get_client
from redis.client import Redis as RedisType

CLIENT: RedisType | None = None


def get_redis_client() -> RedisType:
    """Get a Redis client."""
    global CLIENT

    if CLIENT is not None:
        return CLIENT

    url = os.environ.get("REDIS_URL")
    if not url:
        raise ValueError("REDIS_URL not set")
    CLIENT = get_client(url, socket_keepalive=True)
    return CLIENT

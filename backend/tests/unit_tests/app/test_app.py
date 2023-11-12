"""Test the server and client together."""

import os
from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient
from langchain.utilities.redis import get_client as _get_redis_client
from redis.client import Redis as RedisType
from typing_extensions import AsyncGenerator


@asynccontextmanager
async def get_client() -> AsyncGenerator[AsyncClient, None]:
    """Get the app."""
    from app.server import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def redis_client() -> RedisType:
    """Get a redis client -- and clear it before the test!"""
    redis_url = os.environ.get("REDIS_URL")
    if "localhost" not in redis_url:
        raise ValueError(
            "This test is only intended to be run against a local redis instance"
        )

    if not redis_url.endswith("/3"):
        raise ValueError(
            "This test is only intended to be run against a local redis instance. "
            "For testing purposes this is expected to be database #3 (arbitrary)."
        )

    client = _get_redis_client(redis_url)
    client.flushdb()
    try:
        yield client
    finally:
        client.close()


@pytest.mark.asyncio
async def test_list_and_create_assistants(redis_client: RedisType) -> None:
    """Test list and create assistants."""
    headers = {"Cookie": "opengpts_user_id=1"}
    assert sorted(redis_client.keys()) == []
    async with get_client() as client:
        response = await client.get(
            "/assistants/",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json() == []

        response = await client.put(
            "/assistants/bobby",
            json={"name": "bobby", "config": {}, "public": False},
            headers=headers,
        )
        assert response.status_code == 200
        json_response = response.json()
        assert "updated_at" in json_response
        del json_response["updated_at"]

        assert json_response == {
            "assistant_id": "bobby",
            "config": {},
            "name": "bobby",
            "public": False,
            "user_id": "1",
        }
        assert sorted(redis_client.keys()) == [
            b"opengpts:1:assistant:bobby",
            b"opengpts:1:assistants",
        ]

        assistant_info = redis_client.hgetall("opengpts:1:assistant:bobby")
        del assistant_info[b"updated_at"]
        assert assistant_info == {
            b"assistant_id": b'"bobby"',
            b"config": b"{}",
            b"name": b'"bobby"',
            b"public": b"false",
            b"user_id": b'"1"',
        }


@pytest.mark.asyncio
async def test_list_threads() -> None:
    """Test listing threads."""
    async with get_client() as client:
        response = await client.get(
            "/threads/", headers={"Cookie": "opengpts_user_id=1"}
        )
        assert response.status_code == 200
        assert response.json() == []

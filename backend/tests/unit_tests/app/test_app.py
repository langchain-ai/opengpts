"""Test the server and client together."""

import os
from contextlib import asynccontextmanager
from typing import Optional, Sequence

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


def _project(d: dict, *, exclude_keys: Optional[Sequence[str]]) -> dict:
    """Return a dict with only the keys specified."""
    _exclude = set(exclude_keys) if exclude_keys else set()
    return {k: v for k, v in d.items() if k not in _exclude}


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

        # Create an assistant
        response = await client.put(
            "/assistants/bobby",
            json={"name": "bobby", "config": {}, "public": False},
            headers=headers,
        )
        assert response.status_code == 200
        assert _project(response.json(), exclude_keys=["updated_at"]) == {
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

        response = await client.get("/assistants/", headers=headers)
        assert [_project(d, exclude_keys=["updated_at"]) for d in response.json()] == [
            {
                "assistant_id": "bobby",
                "config": {},
                "name": "bobby",
                "public": False,
            }
        ]

        response = await client.put(
            "/assistants/bobby",
            json={"name": "bobby", "config": {}, "public": False},
            headers=headers,
        )

        assert _project(response.json(), exclude_keys=["updated_at"]) == {
            "assistant_id": "bobby",
            "config": {},
            "name": "bobby",
            "public": False,
            "user_id": "1",
        }

        # Check not visible to other users
        headers = {"Cookie": "opengpts_user_id=2"}
        response = await client.get("/assistants/", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json() == []


async def test_threads(redis_client: RedisType) -> None:
    """Test put thread."""
    async with get_client() as client:
        response = await client.put(
            "/threads/1",
            json={"name": "bobby", "assistant_id": "bobby"},
            headers={"Cookie": "opengpts_user_id=1"},
        )
        assert response.status_code == 200, response.text

        response = await client.get(
            "/threads/1/messages", headers={"Cookie": "opengpts_user_id=1"}
        )
        assert response.status_code == 200
        assert response.json() == {"messages": []}

        response = await client.get(
            "/threads/", headers={"Cookie": "opengpts_user_id=1"}
        )
        assert response.status_code == 200
        assert [_project(d, exclude_keys=["updated_at"]) for d in response.json()] == [
            {
                "assistant_id": "bobby",
                "name": "bobby",
                "thread_id": "1",
            }
        ]

        # Test a bad requests
        response = await client.put(
            "/threads/1",
            json={"name": "bobby", "assistant_id": "bobby"},
        )
        assert response.status_code == 422

        response = await client.put(
            "/threads/1",
            headers={"Cookie": "opengpts_user_id=2"},
        )
        assert response.status_code == 422

        response = await client.get(
            "/threads/",
        )
        assert response.status_code == 422

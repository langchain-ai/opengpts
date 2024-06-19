"""Test the server and client together."""

from typing import Optional, Sequence

from tests.unit_tests.app.helpers import get_client


def _project(d: dict, *, exclude_keys: Optional[Sequence[str]]) -> dict:
    """Return a dict with only the keys specified."""
    _exclude = set(exclude_keys) if exclude_keys else set()
    return {k: v for k, v in d.items() if k not in _exclude}


async def test_list_and_create_assistants() -> None:
    """Test list and create assistants."""
    headers = {"Cookie": "opengpts_user_id=1"}

    async with get_client() as client:
        response = await client.get(
            "/api/assistants/",
            headers=headers,
        )
        assert response.status_code == 200

        assert response.json() == []

        # Create an assistant
        response = await client.post(
            "/api/assistants",
            json={
                "name": "bobby",
                "config": {"configurable": {"type": "chatbot"}},
                "public": False,
            },
            headers=headers,
        )
        assert response.status_code == 200
        aid = response.json()["assistant_id"]
        assert _project(response.json(), exclude_keys=["updated_at", "user_id"]) == {
            "assistant_id": aid,
            "config": {"configurable": {"type": "chatbot"}},
            "name": "bobby",
            "public": False,
        }

        response = await client.get("/api/assistants/", headers=headers)
        assert [
            _project(d, exclude_keys=["updated_at", "user_id"]) for d in response.json()
        ] == [
            {
                "assistant_id": aid,
                "config": {"configurable": {"type": "chatbot"}},
                "name": "bobby",
                "public": False,
            }
        ]

        response = await client.patch(
            f"/api/assistants/{aid}",
            json={"name": "hmmmm"},
            headers=headers,
        )

        assert _project(response.json(), exclude_keys=["updated_at", "user_id"]) == {
            "assistant_id": aid,
            "config": {"configurable": {"type": "chatbot"}},
            "name": "hmmmm",
            "public": False,
        }

        # Check not visible to other users
        headers = {"Cookie": "opengpts_user_id=2"}
        response = await client.get("/api/assistants/", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json() == []

        await client.delete(f"/api/assistants/{aid}", headers=headers)


async def test_threads() -> None:
    """Test put thread."""
    headers = {"Cookie": "opengpts_user_id=1"}

    async with get_client() as client:
        response = await client.post(
            "/api/assistants",
            json={
                "name": "assistant",
                "config": {"configurable": {"type": "chatbot"}},
                "public": False,
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        aid = response.json()["assistant_id"]

        response = await client.post(
            "/api/threads",
            json={"name": "bobby", "assistant_id": aid},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        tid = response.json()["thread_id"]

        response = await client.get(f"/api/threads/{tid}/state", headers=headers)
        assert response.status_code == 200
        assert response.json() == {
            "values": {},
            "next": [],
            "config": {},
            "metadata": {},
            "created_at": None,
            "parent_config": {},
        }

        response = await client.get("/api/threads/", headers=headers)

        assert response.status_code == 200
        assert [
            _project(d, exclude_keys=["updated_at", "user_id"]) for d in response.json()
        ] == [
            {
                "assistant_id": aid,
                "name": "bobby",
                "thread_id": tid,
                "metadata": {},
            }
        ]

        await client.delete(f"/api/threads/{tid}", headers=headers)
        await client.delete(f"/api/assistants/{aid}", headers=headers)

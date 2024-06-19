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
        previous_n = len(response.json())

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
        this_assistant = next(a for a in response.json() if a["assistant_id"] == aid)
        assert _project(this_assistant, exclude_keys=["updated_at", "user_id"]) == {
            "assistant_id": aid,
            "config": {"configurable": {"type": "chatbot"}},
            "name": "bobby",
            "public": False,
        }
        assert len(response.json()) == previous_n + 1

        response = await client.patch(
            f"/api/assistants/{aid}",
            json={"name": "hmmmm"},
            headers=headers,
        )
        assert response.status_code == 200, response.text

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
        assert len(response.json()) == 0

        await client.delete(f"/api/assistants/{aid}", headers=headers)


async def test_threads() -> None:
    """Test put thread."""
    headers = {"Cookie": "opengpts_user_id=1"}

    async with get_client() as client:
        response = await client.get(
            "/api/threads/",
            headers=headers,
        )
        assert response.status_code == 200
        previous_n = len(response.json())

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
        this_thread = next(t for t in response.json() if t["thread_id"] == tid)
        assert _project(this_thread, exclude_keys=["updated_at", "user_id"]) == {
            "thread_id": tid,
            "assistant_id": aid,
            "name": "bobby",
            "metadata": {},
        }
        assert len(response.json()) == previous_n + 1

        await client.delete(f"/api/threads/{tid}", headers=headers)
        await client.delete(f"/api/assistants/{aid}", headers=headers)

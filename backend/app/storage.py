from typing import Any, List, Optional, Sequence, Union

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig

from app.lifespan import get_langserve, get_pg_pool
from app.schema import Assistant, Thread, User


async def list_assistants(user_id: str) -> List[Assistant]:
    """List all assistants for the current user."""
    assistants = await get_langserve().assistants.search(
        metadata={"user_id": user_id}, limit=100
    )
    return [
        Assistant(
            assistant_id=a["assistant_id"],
            updated_at=a["updated_at"],
            config=a["config"],
            **a["metadata"],
        )
        for a in assistants
    ]


async def get_assistant(user_id: str, assistant_id: str) -> Optional[Assistant]:
    """Get an assistant by ID."""
    assistant = await get_langserve().assistants.get(assistant_id)
    if (
        assistant["metadata"]["user_id"] != user_id
        and not assistant["metadata"]["public"]
    ):
        return None
    else:
        return Assistant(
            assistant_id=assistant["assistant_id"],
            updated_at=assistant["updated_at"],
            config=assistant["config"],
            **assistant["metadata"],
        )


async def list_public_assistants() -> List[Assistant]:
    """List all the public assistants."""
    assistants = await get_langserve().assistants.search(metadata={"public": True})
    return [
        Assistant(
            assistant_id=a["assistant_id"],
            updated_at=a["updated_at"],
            config=a["config"],
            **a["metadata"],
        )
        for a in assistants
    ]


async def put_assistant(
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
    assistant = await get_langserve().assistants.upsert(
        assistant_id,
        config["configurable"]["type"],
        config,
        metadata={"user_id": user_id, "public": public, "name": name},
    )
    return Assistant(
        assistant_id=assistant["assistant_id"],
        updated_at=assistant["updated_at"],
        config=assistant["config"],
        name=name,
        public=public,
        user_id=user_id,
    )


async def delete_assistant(user_id: str, assistant_id: str) -> None:
    """Delete an assistant by ID."""
    async with get_pg_pool().acquire() as conn:
        await conn.execute(
            "DELETE FROM assistant WHERE assistant_id = $1 AND user_id = $2",
            assistant_id,
            user_id,
        )


async def list_threads(user_id: str) -> List[Thread]:
    """List all threads for the current user."""
    threads = await get_langserve().threads.search(
        metadata={"user_id": user_id}, limit=100
    )

    return [
        Thread(
            thread_id=t["thread_id"],
            user_id=t["metadata"]["user_id"],
            assistant_id=t["metadata"]["assistant_id"],
            name=t["metadata"]["name"],
            updated_at=t["updated_at"],
        )
        for t in threads
    ]


async def get_thread(user_id: str, thread_id: str) -> Optional[Thread]:
    """Get a thread by ID."""
    thread = await get_langserve().threads.get(thread_id)
    if thread["metadata"]["user_id"] != user_id:
        return None
    else:
        return Thread(
            thread_id=thread["thread_id"],
            user_id=thread["metadata"]["user_id"],
            assistant_id=thread["metadata"]["assistant_id"],
            name=thread["metadata"]["name"],
            updated_at=thread["updated_at"],
        )


async def get_thread_state(*, user_id: str, thread_id: str, assistant: Assistant):
    """Get state for a thread."""
    return await get_langserve().threads.get_state(thread_id)


async def update_thread_state(
    config: RunnableConfig,
    values: Union[Sequence[AnyMessage], dict[str, Any]],
    *,
    user_id: str,
    assistant: Assistant,
):
    """Add state to a thread."""
    return await get_langserve().threads.update_state(config, values)


async def get_thread_history(*, user_id: str, thread_id: str, assistant: Assistant):
    """Get the history of a thread."""
    return await get_langserve().threads.get_history(thread_id)


async def put_thread(
    user_id: str, thread_id: str, *, assistant_id: str, name: str
) -> Thread:
    """Modify a thread."""
    thread = await get_langserve().threads.upsert(
        thread_id,
        metadata={"user_id": user_id, "assistant_id": assistant_id, "name": name},
    )
    return Thread(
        thread_id=thread["thread_id"],
        user_id=thread["metadata"].pop("user_id"),
        assistant_id=thread["metadata"].pop("assistant_id"),
        name=thread["metadata"].pop("name"),
        updated_at=thread["updated_at"],
        metadata=thread["metadata"],
    )


async def delete_thread(user_id: str, thread_id: str):
    """Delete a thread by ID."""
    await get_langserve().threads.delete(thread_id)


async def get_or_create_user(sub: str) -> tuple[User, bool]:
    """Returns a tuple of the user and a boolean indicating whether the user was created."""
    async with get_pg_pool().acquire() as conn:
        if user := await conn.fetchrow('SELECT * FROM "user" WHERE sub = $1', sub):
            return user, False
        user = await conn.fetchrow(
            'INSERT INTO "user" (sub) VALUES ($1) RETURNING *', sub
        )
        return user, True

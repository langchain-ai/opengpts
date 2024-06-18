from typing import Any, Dict, List, Optional, Sequence, Union

from fastapi import HTTPException
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig

from app.lifespan import get_api_client
from app.schema import Assistant, Thread


async def list_assistants(user_id: str) -> List[Assistant]:
    """List all assistants for the current user."""
    assistants = await get_api_client().assistants.search(
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
    assistant = await get_api_client().assistants.get(assistant_id)
    if assistant["metadata"].get("user_id") != user_id and not assistant[
        "metadata"
    ].get("public"):
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
    assistants = await get_api_client().assistants.search(metadata={"public": True})
    return [
        Assistant(
            assistant_id=a["assistant_id"],
            updated_at=a["updated_at"],
            config=a["config"],
            **a["metadata"],
        )
        for a in assistants
    ]


async def create_assistant(
    user_id: str, *, name: str, config: dict, public: bool = False
) -> Assistant:
    """Create an assistant.

    Args:
        user_id: The user ID.
        assistant_id: The assistant ID.
        name: The assistant name.
        config: The assistant config.
        public: Whether the assistant is public.

    Returns:
        return the assistant model if no exception is raised.
    """
    assistant = await get_api_client().assistants.create(
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


async def patch_assistant(
    user_id: str, assistant_id: str, *, name: str, config: dict, public: bool = False
) -> Assistant:
    """Patch an assistant.

    Args:
        user_id: The user ID.
        assistant_id: The assistant ID.
        name: The assistant name.
        config: The assistant config.
        public: Whether the assistant is public.

    Returns:
        return the assistant model if no exception is raised.
    """
    assistant = await get_api_client().assistants.update(
        assistant_id,
        graph_id=config["configurable"]["type"],
        config=config,
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
    assistant = await get_api_client().assistants.get(assistant_id)
    if assistant["metadata"].get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    await get_api_client().assistants.delete(assistant_id)


async def list_threads(user_id: str) -> List[Thread]:
    """List all threads for the current user."""
    threads = await get_api_client().threads.search(
        metadata={"user_id": user_id}, limit=100
    )

    return [
        Thread(
            thread_id=t["thread_id"],
            user_id=t["metadata"].pop("user_id"),
            assistant_id=t["metadata"].pop("assistant_id"),
            name=t["metadata"].pop("name"),
            updated_at=t["updated_at"],
            metadata=t["metadata"],
        )
        for t in threads
    ]


async def get_thread(user_id: str, thread_id: str) -> Optional[Thread]:
    """Get a thread by ID."""
    thread = await get_api_client().threads.get(thread_id)
    if thread["metadata"].get("user_id") != user_id:
        return None
    else:
        return Thread(
            thread_id=thread["thread_id"],
            user_id=thread["metadata"].pop("user_id"),
            assistant_id=thread["metadata"].pop("assistant_id"),
            name=thread["metadata"].pop("name"),
            updated_at=thread["updated_at"],
            metadata=thread["metadata"],
        )


async def get_thread_state(*, user_id: str, thread_id: str, assistant: Assistant):
    """Get state for a thread."""
    return await get_api_client().threads.get_state(thread_id)


async def update_thread_state(
    config: RunnableConfig,
    values: Union[Sequence[AnyMessage], dict[str, Any]],
    *,
    user_id: str,
    assistant: Assistant,
):
    """Add state to a thread."""
    # thread_id (str) must be passed to update_state() instead of config
    # (dict) so that default configs are applied in LangGraph API.
    thread_id = config["configurable"]["thread_id"]
    return await get_api_client().threads.update_state(thread_id, values)


async def patch_thread_state(
    config: RunnableConfig,
    metadata: Dict[str, Any],
):
    """Patch state of a thread."""
    return await get_api_client().threads.patch_state(config, metadata)


async def get_thread_history(*, user_id: str, thread_id: str, assistant: Assistant):
    """Get the history of a thread."""
    return await get_api_client().threads.get_history(thread_id)


async def create_thread(user_id: str, *, assistant_id: str, name: str) -> Thread:
    """Modify a thread."""
    thread = await get_api_client().threads.create(
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


async def patch_thread(
    user_id: str, thread_id: str, *, assistant_id: str, name: str
) -> Thread:
    """Modify a thread."""
    thread = await get_api_client().threads.update(
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
    thread = await get_api_client().threads.get(thread_id)
    if thread["metadata"].get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    await get_api_client().threads.delete(thread_id)

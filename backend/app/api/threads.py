from typing import Annotated, Any, Dict, List, Optional, Sequence, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from langchain.schema.messages import AnyMessage
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

import app.storage as storage
from app.auth.handlers import AuthedUser
from app.schema import Thread

router = APIRouter()


ThreadID = Annotated[str, Path(description="The ID of the thread.")]


class ThreadPostRequest(BaseModel):
    """Payload for creating a thread."""

    name: str = Field(..., description="The name of the thread.")
    assistant_id: str = Field(..., description="The ID of the assistant to use.")
    starting_message: Optional[str] = Field(
        None, description="The starting AI message for the thread."
    )


class ThreadPutRequest(BaseModel):
    """Payload for updating a thread."""

    name: str = Field(..., description="The name of the thread.")
    assistant_id: str = Field(..., description="The ID of the assistant to use.")


class ThreadStatePostRequest(BaseModel):
    """Payload for adding state to a thread."""

    values: Union[Sequence[AnyMessage], Dict[str, Any]]
    config: Optional[Dict[str, Any]] = None


@router.get("/")
async def list_threads(user: AuthedUser) -> List[Thread]:
    """List all threads for the current user."""
    return await storage.list_threads(user["user_id"])


@router.get("/{tid}/state")
async def get_thread_state(
    user: AuthedUser,
    tid: ThreadID,
):
    """Get state for a thread."""
    thread = await storage.get_thread(user["user_id"], tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    assistant = await storage.get_assistant(user["user_id"], thread["assistant_id"])
    if not assistant:
        raise HTTPException(status_code=400, detail="Thread has no assistant")
    return await storage.get_thread_state(
        user_id=user["user_id"],
        thread_id=tid,
        assistant=assistant,
    )


@router.post("/{tid}/state")
async def add_thread_state(
    user: AuthedUser,
    tid: ThreadID,
    payload: ThreadStatePostRequest,
):
    """Add state to a thread."""
    thread = await storage.get_thread(user["user_id"], tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    assistant = await storage.get_assistant(user["user_id"], thread["assistant_id"])
    if not assistant:
        raise HTTPException(status_code=400, detail="Thread has no assistant")
    return await storage.update_thread_state(
        payload.config or {"configurable": {"thread_id": tid}},
        payload.values,
        user_id=user["user_id"],
        assistant=assistant,
    )


@router.get("/{tid}/history")
async def get_thread_history(
    user: AuthedUser,
    tid: ThreadID,
):
    """Get all past states for a thread."""
    thread = await storage.get_thread(user["user_id"], tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    assistant = await storage.get_assistant(user["user_id"], thread["assistant_id"])
    if not assistant:
        raise HTTPException(status_code=400, detail="Thread has no assistant")
    return await storage.get_thread_history(
        user_id=user["user_id"],
        thread_id=tid,
        assistant=assistant,
    )


@router.get("/{tid}")
async def get_thread(
    user: AuthedUser,
    tid: ThreadID,
) -> Thread:
    """Get a thread by ID."""
    thread = await storage.get_thread(user["user_id"], tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("")
async def create_thread(
    user: AuthedUser,
    payload: ThreadPostRequest,
) -> Thread:
    """Create a thread."""
    assistant = await storage.get_assistant(user["user_id"], payload.assistant_id)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    thread = await storage.put_thread(
        user["user_id"],
        str(uuid4()),
        assistant_id=payload.assistant_id,
        name=payload.name,
    )
    if payload.starting_message is not None:
        message = AIMessage(id=str(uuid4()), content=payload.starting_message)
        chat_retrieval = assistant["config"]["configurable"]["type"] == "chat_retrieval"
        await storage.update_thread_state(
            {"configurable": {"thread_id": thread["thread_id"]}},
            {"messages": [message]} if chat_retrieval else [message],
            user_id=user["user_id"],
            assistant=assistant,
        )
    return thread


@router.put("/{tid}")
async def upsert_thread(
    user: AuthedUser,
    tid: ThreadID,
    payload: ThreadPutRequest,
) -> Thread:
    """Update a thread."""
    return await storage.put_thread(
        user["user_id"],
        tid,
        assistant_id=payload.assistant_id,
        name=payload.name,
    )


@router.delete("/{tid}")
async def delete_thread(
    user: AuthedUser,
    tid: ThreadID,
):
    """Delete a thread by ID."""
    await storage.delete_thread(user["user_id"], tid)
    return {"status": "ok"}

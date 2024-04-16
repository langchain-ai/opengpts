import asyncio
from typing import Annotated, Any, Dict, List, Sequence, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from langchain.schema.messages import AnyMessage
from pydantic import BaseModel, Field

import app.storage as storage
from app.auth.handlers import AuthedUser
from app.schema import Thread

router = APIRouter()


ThreadID = Annotated[str, Path(description="The ID of the thread.")]


class ThreadPutRequest(BaseModel):
    """Payload for creating a thread."""

    name: str = Field(..., description="The name of the thread.")
    assistant_id: str = Field(..., description="The ID of the assistant to use.")


class ThreadPostRequest(BaseModel):
    """Payload for adding state to a thread."""

    values: Union[Sequence[AnyMessage], Dict[str, Any]]


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
    thread, state = await asyncio.gather(
        storage.get_thread(user["user_id"], tid),
        storage.get_thread_state(user["user_id"], tid),
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return state


@router.post("/{tid}/state")
async def add_thread_state(
    user: AuthedUser,
    tid: ThreadID,
    payload: ThreadPostRequest,
):
    """Add state to a thread."""
    thread = await storage.get_thread(user["user_id"], tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return await storage.update_thread_state(user["user_id"], tid, payload.values)


@router.get("/{tid}/history")
async def get_thread_history(
    user: AuthedUser,
    tid: ThreadID,
):
    """Get all past states for a thread."""
    thread, history = await asyncio.gather(
        storage.get_thread(user["user_id"], tid),
        storage.get_thread_history(user["user_id"], tid),
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return history


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
    thread_put_request: ThreadPutRequest,
) -> Thread:
    """Create a thread."""
    return await storage.put_thread(
        user["user_id"],
        str(uuid4()),
        assistant_id=thread_put_request.assistant_id,
        name=thread_put_request.name,
    )


@router.put("/{tid}")
async def upsert_thread(
    user: AuthedUser,
    tid: ThreadID,
    thread_put_request: ThreadPutRequest,
) -> Thread:
    """Update a thread."""
    return await storage.put_thread(
        user["user_id"],
        tid,
        assistant_id=thread_put_request.assistant_id,
        name=thread_put_request.name,
    )


@router.delete("/{tid}")
async def delete_thread(
    user: AuthedUser,
    tid: ThreadID,
):
    """Delete a thread by ID."""
    await storage.delete_thread(user["user_id"], tid)
    return {"status": "ok"}

from typing import Annotated, Any, Dict, List, Sequence, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from langchain.schema.messages import AnyMessage
from pydantic import BaseModel, Field

import app.storage as storage
from app.schema import OpengptsUserId, Thread

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
async def list_threads(opengpts_user_id: OpengptsUserId) -> List[Thread]:
    """List all threads for the current user."""
    return await storage.list_threads(opengpts_user_id)


@router.get("/{tid}/state")
async def get_thread_state(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
):
    """Get state for a thread."""
    return await storage.get_thread_state(opengpts_user_id, tid)


@router.post("/{tid}/state")
async def add_thread_state(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
    payload: ThreadPostRequest,
):
    """Add state to a thread."""
    return await storage.update_thread_state(opengpts_user_id, tid, payload.values)


@router.get("/{tid}/history")
async def get_thread_history(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
):
    """Get all past states for a thread."""
    return await storage.get_thread_history(opengpts_user_id, tid)


@router.get("/{tid}")
async def get_thread(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
) -> Thread:
    """Get a thread by ID."""
    thread = await storage.get_thread(opengpts_user_id, tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("")
async def create_thread(
    opengpts_user_id: OpengptsUserId,
    thread_put_request: ThreadPutRequest,
) -> Thread:
    """Create a thread."""
    return await storage.put_thread(
        opengpts_user_id,
        str(uuid4()),
        assistant_id=thread_put_request.assistant_id,
        name=thread_put_request.name,
    )


@router.put("/{tid}")
async def upsert_thread(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
    thread_put_request: ThreadPutRequest,
) -> Thread:
    """Update a thread."""
    return await storage.put_thread(
        opengpts_user_id,
        tid,
        assistant_id=thread_put_request.assistant_id,
        name=thread_put_request.name,
    )

from typing import Annotated, List, Sequence
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from langchain.schema.messages import AnyMessage
from pydantic import BaseModel, Field

import app.storage as storage
from app.schema import OpengptsUserId, Thread, ThreadWithoutUserId

router = APIRouter()


ThreadID = Annotated[str, Path(description="The ID of the thread.")]


class ThreadPutRequest(BaseModel):
    """Payload for creating a thread."""

    name: str = Field(..., description="The name of the thread.")
    assistant_id: str = Field(..., description="The ID of the assistant to use.")


class ThreadMessagesPostRequest(BaseModel):
    """Payload for adding messages to a thread."""

    messages: Sequence[AnyMessage]


@router.get("/")
def list_threads(opengpts_user_id: OpengptsUserId) -> List[ThreadWithoutUserId]:
    """List all threads for the current user."""
    return storage.list_threads(opengpts_user_id)


@router.get("/{tid}/messages")
def get_thread_messages(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
):
    """Get all messages for a thread."""
    return storage.get_thread_messages(opengpts_user_id, tid)


@router.post("/{tid}/messages")
def add_thread_messages(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
    payload: ThreadMessagesPostRequest,
):
    """Add messages to a thread."""
    return storage.post_thread_messages(opengpts_user_id, tid, payload.messages)


@router.get("/{tid}")
def get_thread(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
) -> Thread:
    """Get a thread by ID."""
    thread = storage.get_thread(opengpts_user_id, tid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("")
def create_thread(
    opengpts_user_id: OpengptsUserId,
    thread_put_request: ThreadPutRequest,
) -> Thread:
    """Create a thread."""
    return storage.put_thread(
        opengpts_user_id,
        str(uuid4()),
        assistant_id=thread_put_request.assistant_id,
        name=thread_put_request.name,
    )


@router.put("/{tid}")
def upsert_thread(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
    thread_put_request: ThreadPutRequest,
) -> Thread:
    """Update a thread."""
    return storage.put_thread(
        opengpts_user_id,
        tid,
        assistant_id=thread_put_request.assistant_id,
        name=thread_put_request.name,
    )

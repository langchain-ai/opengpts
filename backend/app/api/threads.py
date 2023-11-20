from typing import Annotated, List

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

import app.storage as storage
from app.schema import OpengptsUserId, Thread, ThreadWithoutUserId

router = APIRouter()


ThreadID = Annotated[str, Path(description="The ID of the thread.")]


class ThreadPutRequest(BaseModel):
    """Payload for creating a thread."""

    name: str = Field(..., description="The name of the thread.")
    assistant_id: str = Field(..., description="The ID of the assistant to use.")


@router.get("/")
def list_threads_endpoint(
    opengpts_user_id: OpengptsUserId
) -> List[ThreadWithoutUserId]:
    """List all threads for the current user."""
    return storage.list_threads(opengpts_user_id)


@router.get("/{tid}/messages")
def get_thread_messages_endpoint(
    opengpts_user_id: OpengptsUserId,
    tid: ThreadID,
):
    """Get all messages for a thread."""
    return storage.get_thread_messages(opengpts_user_id, tid)


@router.put("/{tid}")
def put_thread_endpoint(
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

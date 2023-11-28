from typing import Annotated, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query, Cookie
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

import app.storage as storage
from app.schema import Assistant, AssistantWithoutUserId, OpengptsUserId

router = APIRouter()

FEATURED_PUBLIC_ASSISTANTS = [
    "ba721964-b7e4-474c-b817-fb089d94dc5f",
    "dc3ec482-aafc-4d90-8a1a-afb9b2876cde",
]


class AssistantPayload(BaseModel):
    """Payload for creating an assistant."""

    name: str = Field(..., description="The name of the assistant.")
    config: dict = Field(..., description="The assistant config.")
    public: bool = Field(default=False, description="Whether the assistant is public.")


class PublicPayload(TypedDict):
    public: bool


AssistantID = Annotated[str, Path(description="The ID of the assistant.")]


@router.get("/")
def list_assistants(opengpts_user_id: OpengptsUserId) -> List[AssistantWithoutUserId]:
    """List all assistants for the current user."""
    return storage.list_assistants(opengpts_user_id)


@router.get("/public/")
def list_public_assistants(
    shared_id: Annotated[
        Optional[str], Query(description="ID of a publicly shared assistant.")
    ] = None,
) -> List[AssistantWithoutUserId]:
    """List all public assistants."""
    return storage.list_public_assistants(
        FEATURED_PUBLIC_ASSISTANTS + ([shared_id] if shared_id else [])
    )


@router.get("/{aid}")
def get_asistant(
    opengpts_user_id: OpengptsUserId,
    aid: AssistantID,
) -> Assistant:
    """Get an assistant by ID."""
    assistant = storage.get_assistant(opengpts_user_id, aid)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


@router.post("")
def create_assistant(
    opengpts_user_id: OpengptsUserId,
    payload: AssistantPayload,
) -> Assistant:
    """Create an assistant."""
    return storage.put_assistant(
        opengpts_user_id,
        str(uuid4()),
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )


@router.put("/{aid}")
def upsert_assistant(
    opengpts_user_id: OpengptsUserId,
    aid: AssistantID,
    payload: AssistantPayload,
) -> Assistant:
    """Create or update an assistant."""
    return storage.put_assistant(
        opengpts_user_id,
        aid,
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )

@router.delete("/{aid}")
def delete_assistant_endpoint(
    aid: str,
    payload: PublicPayload,
    opengpts_user_id: Annotated[str, Cookie()],
):
    return storage.delete_assistant(
        opengpts_user_id,
        aid,
        payload["public"],
    )


from typing import Annotated, List, Optional

from fastapi import APIRouter, Cookie, Path, Query
from pydantic import BaseModel, Field

import app.storage as storage
from app.schema import Assistant, AssistantWithoutUserId, OpengptsUserId

router = APIRouter()

FEATURED_PUBLIC_ASSISTANTS = [
    "ba721964-b7e4-474c-b817-fb089d94dc5f",
    "dc3ec482-aafc-4d90-8a1a-afb9b2876cde",
]


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


class AssistantPayload(BaseModel):
    """Payload for creating an assistant."""

    name: str = Field(..., description="The name of the assistant.")
    config: dict = Field(..., description="The assistant config.")
    public: bool = Field(default=False, description="Whether the assistant is public.")


AssistantID = Annotated[str, Path(description="The ID of the assistant.")]


@router.put("/{aid}")
def put_assistant(
    opengpts_user_id: Annotated[str, Cookie()],
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

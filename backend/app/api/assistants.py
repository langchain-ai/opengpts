from typing import Annotated, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

import app.storage as storage
from app.auth.handlers import AuthedUser
from app.schema import Assistant

router = APIRouter()

FEATURED_PUBLIC_ASSISTANTS = []


class AssistantPayload(BaseModel):
    """Payload for creating an assistant."""

    name: str = Field(..., description="The name of the assistant.")
    config: dict = Field(..., description="The assistant config.")
    public: bool = Field(default=False, description="Whether the assistant is public.")


AssistantID = Annotated[str, Path(description="The ID of the assistant.")]


@router.get("/")
async def list_assistants(user: AuthedUser) -> List[Assistant]:
    """List all assistants for the current user."""
    return await storage.list_assistants(user["user_id"])


@router.get("/public/")
async def list_public_assistants(
    shared_id: Annotated[
        Optional[str], Query(description="ID of a publicly shared assistant.")
    ] = None,
) -> List[Assistant]:
    """List all public assistants."""
    return await storage.list_public_assistants(
        FEATURED_PUBLIC_ASSISTANTS + ([shared_id] if shared_id else [])
    )


@router.get("/{aid}")
async def get_assistant(
    user: AuthedUser,
    aid: AssistantID,
) -> Assistant:
    """Get an assistant by ID."""
    assistant = await storage.get_assistant(user["user_id"], aid)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


@router.post("")
async def create_assistant(
    user: AuthedUser,
    payload: AssistantPayload,
) -> Assistant:
    """Create an assistant."""
    return await storage.put_assistant(
        user["user_id"],
        str(uuid4()),
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )


@router.put("/{aid}")
async def upsert_assistant(
    user: AuthedUser,
    aid: AssistantID,
    payload: AssistantPayload,
) -> Assistant:
    """Create or update an assistant."""
    return await storage.put_assistant(
        user["user_id"],
        aid,
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )

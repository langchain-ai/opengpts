from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

import app.storage as storage
from app.auth.handlers import AuthedUser
from app.schema import Assistant

router = APIRouter()


class AssistantPayload(BaseModel):
    """Payload for creating an assistant."""

    name: str = Field(..., description="The name of the assistant.")
    config: dict = Field(..., description="The assistant config.")
    public: bool = Field(default=False, description="Whether the assistant is public.")


class AssistantPatch(BaseModel):
    """Payload for creating an assistant."""

    name: str | None = Field(None, description="The name of the assistant.")
    config: dict | None = Field(None, description="The assistant config.")
    public: bool | None = Field(None, description="Whether the assistant is public.")


AssistantID = Annotated[str, Path(description="The ID of the assistant.")]


@router.get("/")
async def list_assistants(user: AuthedUser) -> List[Assistant]:
    """List all assistants for the current user."""
    return await storage.list_assistants(user["user_id"])


@router.get("/public/")
async def list_public_assistants() -> List[Assistant]:
    """List all public assistants."""
    return await storage.list_public_assistants()


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
    if not payload.config.get("configurable", {}).get("type"):
        raise HTTPException(
            status_code=400, detail="Assistant config must have configurable.type field"
        )
    return await storage.create_assistant(
        user["user_id"],
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )


@router.patch("/{aid}")
async def patch_assistant(
    user: AuthedUser,
    aid: AssistantID,
    payload: AssistantPatch,
) -> Assistant:
    """Create or update an assistant."""
    if payload.config and not payload.config.get("configurable", {}).get("type"):
        raise HTTPException(
            status_code=400, detail="Assistant config must have configurable.type field"
        )

    return await storage.patch_assistant(
        user["user_id"],
        aid,
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )


@router.delete("/{aid}")
async def delete_assistant(
    user: AuthedUser,
    aid: AssistantID,
):
    """Delete an assistant by ID."""
    await storage.delete_assistant(user["user_id"], aid)
    return {"status": "ok"}

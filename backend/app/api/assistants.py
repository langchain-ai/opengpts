from typing import Annotated, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query
from langsmith import Client as LangSmithClient
from pydantic import BaseModel, Field

import app.storage as storage
from app.schema import Assistant, OpengptsUserId

router = APIRouter()

FEATURED_PUBLIC_ASSISTANTS = []
LANGSMITH_CLIENT = LangSmithClient()
LANGSMITH_SESSION_ID = "37f535e9-22c4-4267-9d36-522930e59cb7"


class AssistantPayload(BaseModel):
    """Payload for creating an assistant."""

    name: str = Field(..., description="The name of the assistant.")
    config: dict = Field(..., description="The assistant config.")
    public: bool = Field(default=False, description="Whether the assistant is public.")


AssistantID = Annotated[str, Path(description="The ID of the assistant.")]


@router.get("/")
async def list_assistants(opengpts_user_id: OpengptsUserId) -> List[Assistant]:
    """List all assistants for the current user."""
    return await storage.list_assistants(opengpts_user_id)


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
    opengpts_user_id: OpengptsUserId,
    aid: AssistantID,
) -> Assistant:
    """Get an assistant by ID."""
    assistant = await storage.get_assistant(opengpts_user_id, aid)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


@router.post("")
async def create_assistant(
    opengpts_user_id: OpengptsUserId,
    payload: AssistantPayload,
) -> Assistant:
    """Create an assistant."""
    return await storage.put_assistant(
        opengpts_user_id,
        str(uuid4()),
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )


def _create_few_shot_dataset_and_rule(
    aid: AssistantID, assistant_type: Literal["agent", "chatbot"]
) -> None:
    dataset = LANGSMITH_CLIENT.create_dataset(aid)
    user_liked_filter = f'and(eq(feedback_key, "user_score"), eq(feedback_score, 1), eq(metadata_key, "assistant_id"), eq(metadata_value, "{aid}"))'
    payload = {
        "display_name": f"few shot {aid}",
        "session_id": LANGSMITH_SESSION_ID,
        "sampling_rate": 1,
        "add_to_dataset_id": str(dataset.id),
    }
    if assistant_type == "agent":
        payload["filter"] = user_liked_filter
    elif assistant_type == "chatbot":
        payload["filter"] = 'eq(name, "chatbot")'
        payload["trace_filter"] = user_liked_filter
    else:
        raise ValueError(
            f"Unknown assistant_type {assistant_type}. Expected 'agent' or 'chatbot'."
        )
    LANGSMITH_CLIENT.request_with_retries(
        "POST",
        LANGSMITH_CLIENT.api_url + "/runs/rules",
        {"json": payload, "headers": LANGSMITH_CLIENT._headers},
    )


@router.put("/{aid}")
async def upsert_assistant(
    opengpts_user_id: OpengptsUserId,
    aid: AssistantID,
    payload: AssistantPayload,
) -> Assistant:
    """Create or update an assistant."""
    assistant_type = payload.config["configurable"]["type"]
    if payload.config["configurable"]["type"] in ("chatbot", "agent"):
        _create_few_shot_dataset_and_rule(aid, assistant_type)
    return await storage.put_assistant(
        opengpts_user_id,
        aid,
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )

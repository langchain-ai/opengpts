from typing import Annotated, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field
from langsmith import Client as LangSmithClient

import app.storage as storage
from app.schema import Assistant, AssistantWithoutUserId, OpengptsUserId

router = APIRouter()

FEATURED_PUBLIC_ASSISTANTS = []
LANGSMITHCLIENT = LangSmithClient()


class AssistantPayload(BaseModel):
    """Payload for creating an assistant."""

    name: str = Field(..., description="The name of the assistant.")
    config: dict = Field(..., description="The assistant config.")
    public: bool = Field(default=False, description="Whether the assistant is public.")


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
    LANGSMITHCLIENT.create_dataset(aid)
    LANGSMITHCLIENT.request_with_retries(
      "POST",
      LANGSMITHCLIENT.api_url + "/runs/rules",
      {
        "json": {
          "display_name": "queries",
          "session_id": "942208fa-21ee-4ed8-ab5d-6ed5a9090cdf",
          "sampling_rate": 1,
          "filter": 'eq(name, "chatbot")',
          "trace_filter": f'and(and(eq(feedback_key, "user_score"), eq(feedback_score, 1)), and(eq(metadata_key, "assistant_id"), eq(metadata_value, "{aid}")))',
          "add_to_dataset_id": aid
        },
        "headers": LANGSMITHCLIENT._headers
      }
    )
    return storage.put_assistant(
        opengpts_user_id,
        aid,
        name=payload.name,
        config=payload.config,
        public=payload.public,
    )

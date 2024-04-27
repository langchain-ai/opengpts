import json
from typing import Any, Dict, Optional, Sequence, Union
from uuid import UUID

import langsmith.client
from fastapi import APIRouter, HTTPException
from langchain_core.runnables import RunnableConfig
from langsmith.utils import tracing_is_enabled
from pydantic import BaseModel, Field
from sse_starlette import EventSourceResponse

from app.agent import agent
from app.auth.handlers import AuthedUser
from app.storage import get_thread
from app.lifespan import get_langserve

router = APIRouter()


class CreateRunPayload(BaseModel):
    """Payload for creating a run."""

    thread_id: str
    input: Optional[Union[Sequence[dict], Dict[str, Any]]] = Field(default_factory=dict)
    config: Optional[RunnableConfig] = None


@router.post("")
async def create_run(payload: CreateRunPayload, user: AuthedUser):
    """Create a run."""
    thread = await get_thread(user["user_id"], payload.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return await get_langserve().runs.create(
        payload.thread_id,
        thread["assistant_id"],
        input=payload.input,
        config=payload.config,
    )


@router.post("/stream")
async def stream_run(
    payload: CreateRunPayload,
    user: AuthedUser,
):
    """Create a run."""
    thread = await get_thread(user["user_id"], payload.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return EventSourceResponse(
        (
            {"event": e.event, "data": json.dumps(e.data)}
            async for e in get_langserve().runs.stream(
                payload.thread_id,
                thread["assistant_id"],
                input=payload.input,
                config=payload.config,
            )
        )
    )


@router.get("/input_schema")
async def input_schema() -> dict:
    """Return the input schema of the runnable."""
    return agent.get_input_schema().schema()


@router.get("/output_schema")
async def output_schema() -> dict:
    """Return the output schema of the runnable."""
    return agent.get_output_schema().schema()


@router.get("/config_schema")
async def config_schema() -> dict:
    """Return the config schema of the runnable."""
    return agent.config_schema().schema()


if tracing_is_enabled():
    langsmith_client = langsmith.client.Client()

    class FeedbackCreateRequest(BaseModel):
        """
        Shared information between create requests of feedback and feedback objects
        """

        run_id: UUID
        """The associated run ID this feedback is logged for."""

        key: str
        """The metric name, tag, or aspect to provide feedback on."""

        score: Optional[Union[float, int, bool]] = None
        """Value or score to assign the run."""

        value: Optional[Union[float, int, bool, str, Dict]] = None
        """The display value for the feedback if not a metric."""

        comment: Optional[str] = None
        """Comment or explanation for the feedback."""

    @router.post("/feedback")
    def create_run_feedback(feedback_create_req: FeedbackCreateRequest) -> dict:
        """
        Send feedback on an individual run to langsmith

        Note that a successful response means that feedback was successfully
        submitted. It does not guarantee that the feedback is recorded by
        langsmith. Requests may be silently rejected if they are
        unauthenticated or invalid by the server.
        """

        langsmith_client.create_feedback(
            feedback_create_req.run_id,
            feedback_create_req.key,
            score=feedback_create_req.score,
            value=feedback_create_req.value,
            comment=feedback_create_req.comment,
            source_info={
                "from_langserve": True,
            },
        )

        return {"status": "ok"}

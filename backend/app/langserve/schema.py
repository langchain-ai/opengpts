from datetime import datetime
from typing import Any, Literal, Optional, Sequence, Union, TypedDict

from pydantic import BaseModel, Field


Metadata = Optional[dict[str, Any]]

RunStatus = Literal["pending", "running", "error", "success", "timeout", "interrupted"]

StreamMode = Literal["values", "messages", "updates", "events"]


class Config(TypedDict, total=False):
    tags: list[str]
    """
    Tags for this call and any sub-calls (eg. a Chain calling an LLM).
    You can use these to filter calls.
    """

    recursion_limit: int
    """
    Maximum number of times a call can recurse. If not provided, defaults to 25.
    """

    configurable: dict[str, Any]
    """
    Runtime values for attributes previously made configurable on this Runnable,
    or sub-Runnables, through .configurable_fields() or .configurable_alternatives().
    Check .output_schema() for a description of the attributes that have been made 
    configurable.
    """


class Assistant(TypedDict):
    """Assistant model."""

    assistant_id: str
    """The ID of the assistant."""
    graph_id: Optional[str]
    """The ID of the graph."""
    config: Config
    """The assistant config."""
    created_at: datetime
    """The time the assistant was created."""
    updated_at: datetime
    """The last time the assistant was updated."""
    metadata: Metadata
    """The assistant metadata."""


class Thread(TypedDict):
    thread_id: str
    """The ID of the thread."""
    created_at: datetime
    """The time the thread was created."""
    updated_at: datetime
    """The last time the thread was updated."""
    metadata: Metadata
    """The thread metadata."""


class JsonMessage(TypedDict):
    role: str
    """The role of the message."""
    content: str
    """The content of the message."""


class ThreadState(TypedDict):
    values: Union[list[JsonMessage], dict[str, Any]]
    """The state values."""
    next: Sequence[str]
    """The next nodes to execute. If empty, the thread is done until new input is 
    received."""
    config: Config
    """Config used to fetch/use this state"""
    parent_config: Optional[Config] = None
    """Config used to fetch the parent state, if any"""


class Run(TypedDict):
    run_id: str
    """The ID of the run."""
    thread_id: str
    """The ID of the thread."""
    assistant_id: str
    """The assistant that was used for this run."""
    created_at: datetime
    """The time the run was created."""
    updated_at: datetime
    """The last time the run was updated."""
    status: RunStatus
    """The status of the run. One of 'pending', 'running', 'error', 'success'."""
    metadata: Metadata
    """The run metadata."""


class RunEvent(TypedDict):
    event_id: str
    """The ID of the event."""
    run_id: str
    """The ID of the run."""
    received_at: datetime
    """The time the event was received."""
    span_id: str
    """The ID of the span."""
    event: str
    """The event type."""
    name: str
    """The event name."""
    data: dict
    """The event data."""
    metadata: dict
    """The event metadata."""
    tags: list[str]
    """The event tags."""


class SearchRequest(BaseModel):
    """Payload for listing assistants/threads/runs."""

    metadata: Metadata = Field(None, description="Metadata to search for.")
    limit: int = Field(10, description="Maximum number to return.")
    offset: int = Field(0, description="Offset to start from.")

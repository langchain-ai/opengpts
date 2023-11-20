from datetime import datetime

from typing_extensions import TypedDict


class AssistantWithoutUserId(TypedDict):
    """Assistant model."""

    assistant_id: str
    """The ID of the assistant."""
    name: str
    """The name of the assistant."""
    config: dict
    """The assistant config."""
    updated_at: datetime
    """The last time the assistant was updated."""
    public: bool
    """Whether the assistant is public."""


class Assistant(AssistantWithoutUserId):
    """Assistant model."""

    user_id: str
    """The ID of the user that owns the assistant."""


class ThreadWithoutUserId(TypedDict):
    thread_id: str
    """The ID of the thread."""
    assistant_id: str
    """The assistant that was used in conjunction with this thread."""
    name: str
    """The name of the thread."""
    updated_at: datetime
    """The last time the thread was updated."""


class Thread(ThreadWithoutUserId):
    """Thread model."""

    user_id: str
    """The ID of the user that owns the thread."""

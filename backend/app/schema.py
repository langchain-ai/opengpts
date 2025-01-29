from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    """The ID of the user."""
    sub: str
    """The sub of the user (from a JWT token)."""
    created_at: datetime
    """The time the user was created."""


class Assistant(BaseModel):
    assistant_id: str
    """The ID of the assistant."""
    user_id: str
    """The ID of the user that owns the assistant."""
    name: str
    """The name of the assistant."""
    config: dict
    """The assistant config."""
    updated_at: datetime
    """The last time the assistant was updated."""
    public: bool = False
    """Whether the assistant is public."""


class Thread(BaseModel):
    thread_id: str
    """The ID of the thread."""
    user_id: str
    """The ID of the user that owns the thread."""
    assistant_id: Optional[str] = None
    """The assistant that was used in conjunction with this thread."""
    name: str
    """The name of the thread."""
    updated_at: datetime
    """The last time the thread was updated."""
    metadata: Optional[dict] = None

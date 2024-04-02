from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID
from fastapi import Cookie
from typing_extensions import TypedDict

from pydantic import BaseModel
from datetime import datetime


class Assistant(TypedDict):
    """Assistant model."""

    assistant_id: UUID
    """The ID of the assistant."""
    user_id: str
    """The ID of the user that owns the assistant."""
    name: str
    """The name of the assistant."""
    config: dict
    """The assistant config."""
    updated_at: datetime
    """The last time the assistant was updated."""
    public: bool
    """Whether the assistant is public."""


class Thread(TypedDict):
    thread_id: UUID
    """The ID of the thread."""
    user_id: str
    """The ID of the user that owns the thread."""
    assistant_id: Optional[UUID]
    """The assistant that was used in conjunction with this thread."""
    name: str
    """The name of the thread."""
    updated_at: datetime
    """The last time the thread was updated."""

class User(BaseModel):
    """User model"""

    user_id: UUID
    """The ID of the user."""
    username: str
    """The username of the user."""
    password_hash: str
    """The hashed password of the user."""
    email: str
    """The email address of the user."""
    full_name: str
    """The full name of the user."""
    address: str
    """The address of the user."""
    creation_date: datetime
    """The date and time when the user account was created."""
    last_login_date: Optional[datetime] = None
    """The date and time when the user last logged in. Can be None initially."""
    is_active: bool
    """Boolean flag indicating whether the user account is active."""
    is_deleted: bool = False
    """indicate if the user is deleted"""


OpengptsUserId = Annotated[
    str,
    Cookie(
        description=(
            "A cookie that identifies the user. This is not an authentication "
            "mechanism that should be used in an actual production environment that "
            "contains sensitive information."
        )
    ),
]

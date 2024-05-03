from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence, Union

from langchain_core.messages import AnyMessage

from app.schema import Assistant, Thread, User


class BaseStorage(ABC):
    @abstractmethod
    async def setup(self) -> None:
        """Setup the storage."""

    @abstractmethod
    async def teardown(self) -> None:
        """Teardown the storage."""

    @abstractmethod
    async def list_assistants(self, user_id: str) -> list[Assistant]:
        """List all assistants for the current user."""

    @abstractmethod
    async def get_assistant(
        self, user_id: str, assistant_id: str
    ) -> Optional[Assistant]:
        """Get an assistant by ID."""

    @abstractmethod
    async def list_public_assistants(
        self, assistant_ids: Sequence[str]
    ) -> list[Assistant]:
        """List all the public assistants."""

    @abstractmethod
    async def put_assistant(
        self,
        user_id: str,
        assistant_id: str,
        *,
        name: str,
        config: dict,
        public: bool = False,
    ) -> Assistant:
        """Modify an assistant."""

    @abstractmethod
    async def list_threads(self, user_id: str) -> list[Thread]:
        """List all threads for the current user."""

    @abstractmethod
    async def get_thread(self, user_id: str, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""

    @abstractmethod
    async def get_thread_state(self, user_id: str, thread_id: str):
        """Get state for a thread."""

    @abstractmethod
    async def update_thread_state(
        self,
        user_id: str,
        thread_id: str,
        values: Union[Sequence[AnyMessage], dict[str, Any]],
    ):
        """Add state to a thread."""

    @abstractmethod
    async def get_thread_history(self, user_id: str, thread_id: str):
        """Get the history of a thread."""

    @abstractmethod
    async def put_thread(
        self, user_id: str, thread_id: str, *, assistant_id: str, name: str
    ) -> Thread:
        """Modify a thread."""

    @abstractmethod
    async def get_or_create_user(self, sub: str) -> tuple[User, bool]:
        """Returns a tuple of the user and a boolean indicating whether the user was created."""

    @abstractmethod
    async def delete_thread(self, user_id: str, thread_id: str) -> None:
        """Delete a thread by ID."""

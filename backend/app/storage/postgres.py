from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence, Union

import asyncpg
import orjson
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig

from app.schema import Assistant, Thread, User
from app.storage.base import BaseStorage
from app.storage.settings import settings as storage_settings


class PostgresStorage(BaseStorage):
    _pg_pool: asyncpg.pool.Pool = None
    _is_setup: bool = False

    async def setup(self) -> None:
        if self._is_setup:
            return
        self._pg_pool = await asyncpg.create_pool(
            database=storage_settings.postgres.db,
            user=storage_settings.postgres.user,
            password=storage_settings.postgres.password,
            host=storage_settings.postgres.host,
            port=storage_settings.postgres.port,
            init=self._init_connection,
        )
        self._is_setup = True

    async def teardown(self) -> None:
        await self._pg_pool.close()
        self._pg_pool = None
        self._is_setup = False

    async def _init_connection(self, conn) -> None:
        await conn.set_type_codec(
            "json",
            encoder=lambda v: orjson.dumps(v).decode(),
            decoder=orjson.loads,
            schema="pg_catalog",
        )
        await conn.set_type_codec(
            "uuid", encoder=lambda v: str(v), decoder=lambda v: v, schema="pg_catalog"
        )

    def get_pg_pool(self) -> asyncpg.pool.Pool:
        return self._pg_pool

    async def list_assistants(self, user_id: str) -> List[Assistant]:
        """List all assistants for the current user."""
        async with self.get_pg_pool().acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM assistant WHERE user_id = $1", user_id
            )

    async def get_assistant(
        self, user_id: str, assistant_id: str
    ) -> Optional[Assistant]:
        """Get an assistant by ID."""
        async with self.get_pg_pool().acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM assistant WHERE assistant_id = $1 AND (user_id = $2 OR public IS true)",
                assistant_id,
                user_id,
            )

    async def list_public_assistants(self) -> List[Assistant]:
        """List all the public assistants."""
        async with self.get_pg_pool().acquire() as conn:
            return await conn.fetch(("SELECT * FROM assistant WHERE public IS true;"))

    async def put_assistant(
        self,
        user_id: str,
        assistant_id: str,
        *,
        name: str,
        config: dict,
        public: bool = False,
    ) -> Assistant:
        """Modify an assistant.

        Args:
            user_id: The user ID.
            assistant_id: The assistant ID.
            name: The assistant name.
            config: The assistant config.
            public: Whether the assistant is public.

        Returns:
            return the assistant model if no exception is raised.
        """
        updated_at = datetime.now(timezone.utc)
        async with self.get_pg_pool().acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    (
                        "INSERT INTO assistant (assistant_id, user_id, name, config, updated_at, public) VALUES ($1, $2, $3, $4, $5, $6) "
                        "ON CONFLICT (assistant_id) DO UPDATE SET "
                        "user_id = EXCLUDED.user_id, "
                        "name = EXCLUDED.name, "
                        "config = EXCLUDED.config, "
                        "updated_at = EXCLUDED.updated_at, "
                        "public = EXCLUDED.public;"
                    ),
                    assistant_id,
                    user_id,
                    name,
                    config,
                    updated_at,
                    public,
                )
        return {
            "assistant_id": assistant_id,
            "user_id": user_id,
            "name": name,
            "config": config,
            "updated_at": updated_at,
            "public": public,
        }

    async def list_threads(self, user_id: str) -> List[Thread]:
        """List all threads for the current user."""
        async with self.get_pg_pool().acquire() as conn:
            return await conn.fetch("SELECT * FROM thread WHERE user_id = $1", user_id)

    async def get_thread(self, user_id: str, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        async with self.get_pg_pool().acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM thread WHERE thread_id = $1 AND user_id = $2",
                thread_id,
                user_id,
            )

    async def get_thread_state(
        self, *, user_id: str, thread_id: str, assistant_id: str
    ):
        """Get state for a thread."""
        from app.agent import agent

        assistant = await self.get_assistant(user_id, assistant_id)
        state = await agent.aget_state(
            {
                "configurable": {
                    **assistant["config"]["configurable"],
                    "thread_id": thread_id,
                    "assistant_id": assistant_id,
                }
            }
        )
        return {
            "values": state.values,
            "next": state.next,
        }

    async def update_thread_state(
        self,
        config: RunnableConfig,
        values: Union[Sequence[AnyMessage], dict[str, Any]],
        *,
        user_id: str,
        assistant_id: str,
    ):
        """Add state to a thread."""
        from app.agent import agent

        assistant = await self.get_assistant(user_id, assistant_id)
        await agent.aupdate_state(
            {
                "configurable": {
                    **assistant["config"]["configurable"],
                    **config["configurable"],
                    "assistant_id": assistant_id,
                }
            },
            values,
        )

    async def get_thread_history(
        self, *, user_id: str, thread_id: str, assistant_id: str
    ):
        """Get the history of a thread."""
        from app.agent import agent

        assistant = await self.get_assistant(user_id, assistant_id)
        return [
            {
                "values": c.values,
                "next": c.next,
                "config": c.config,
                "parent": c.parent_config,
            }
            async for c in agent.aget_state_history(
                {
                    "configurable": {
                        **assistant["config"]["configurable"],
                        "thread_id": thread_id,
                        "assistant_id": assistant_id,
                    }
                }
            )
        ]

    async def put_thread(
        self, user_id: str, thread_id: str, *, assistant_id: str, name: str
    ) -> Thread:
        """Modify a thread."""
        updated_at = datetime.now(timezone.utc)
        async with self.get_pg_pool().acquire() as conn:
            await conn.execute(
                (
                    "INSERT INTO thread (thread_id, user_id, assistant_id, name, updated_at) VALUES ($1, $2, $3, $4, $5) "
                    "ON CONFLICT (thread_id) DO UPDATE SET "
                    "user_id = EXCLUDED.user_id,"
                    "assistant_id = EXCLUDED.assistant_id, "
                    "name = EXCLUDED.name, "
                    "updated_at = EXCLUDED.updated_at;"
                ),
                thread_id,
                user_id,
                assistant_id,
                name,
                updated_at,
            )
            return {
                "thread_id": thread_id,
                "user_id": user_id,
                "assistant_id": assistant_id,
                "name": name,
                "updated_at": updated_at,
            }

    async def get_or_create_user(self, sub: str) -> tuple[User, bool]:
        """Returns a tuple of the user and a boolean indicating whether the user was created."""
        async with self.get_pg_pool().acquire() as conn:
            user = await conn.fetchrow(
                'INSERT INTO "user" (sub) VALUES ($1) ON CONFLICT (sub) DO NOTHING RETURNING *',
                sub,
            )
            if user:
                return user, True
            user = await conn.fetchrow('SELECT * FROM "user" WHERE sub = $1', sub)
            return user, False

    async def delete_thread(self, user_id: str, thread_id: str) -> None:
        """Delete a thread by ID."""
        async with self.get_pg_pool().acquire() as conn:
            await conn.execute(
                "DELETE FROM thread WHERE thread_id = $1 AND user_id = $2",
                thread_id,
                user_id,
            )

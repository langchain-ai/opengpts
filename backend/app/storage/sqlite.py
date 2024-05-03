import json
from datetime import datetime, timezone
from typing import Any, Optional, Sequence, Union
from uuid import uuid4

import aiosqlite
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig

from app.schema import Assistant, Thread, User
from app.storage.base import BaseStorage


def _deserialize_assistant(row: aiosqlite.Row) -> Assistant:
    """Deserialize an assistant from a SQLite row."""
    return {
        "assistant_id": row["assistant_id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "config": json.loads(row["config"]),
        "updated_at": datetime.fromisoformat(row["updated_at"]),
        "public": bool(row["public"]),
    }


def _deserialize_thread(row: aiosqlite.Row) -> Thread:
    """Deserialize a thread from a SQLite row."""
    return {
        "thread_id": row["thread_id"],
        "user_id": row["user_id"],
        "assistant_id": row["assistant_id"],
        "name": row["name"],
        "updated_at": datetime.fromisoformat(row["updated_at"]),
    }


def _deserialize_user(row: aiosqlite.Row) -> User:
    """Deserialize a user from a SQLite row."""
    return {
        "user_id": row["user_id"],
        "sub": row["sub"],
        "created_at": datetime.fromisoformat(row["created_at"]),
    }


class SqliteStorage(BaseStorage):
    _conn: aiosqlite.Connection = None
    _is_setup: bool = False

    async def setup(self) -> None:
        if self._is_setup:
            return
        self._conn = await aiosqlite.connect("opengpts.db")
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("pragma journal_mode=wal")
        self._is_setup = True

        # TODO remove
        await self._conn.set_trace_callback(print)

    async def teardown(self) -> None:
        await self._conn.close()
        self._conn = None
        self._is_setup = False

    def get_conn(self) -> aiosqlite.Connection:
        if not self._is_setup:
            raise RuntimeError("Storage is not set up.")
        return self._conn

    async def list_assistants(self, user_id: str) -> list[Assistant]:
        """List all assistants for the current user."""
        async with self.get_conn().cursor() as cur:
            await cur.execute("SELECT * FROM assistant WHERE user_id = ?", (user_id,))
            rows = await cur.fetchall()
            return [_deserialize_assistant(row) for row in rows]

    async def get_assistant(
        self, user_id: str, assistant_id: str
    ) -> Optional[Assistant]:
        """Get an assistant by ID."""
        async with self.get_conn().cursor() as cur:
            await cur.execute(
                "SELECT * FROM assistant WHERE assistant_id = ? AND (user_id = ? OR public = 1)",
                (assistant_id, user_id),
            )
            row = await cur.fetchone()
            return _deserialize_assistant(row) if row else None

    async def list_public_assistants(self) -> list[Assistant]:
        """List all the public assistants."""
        async with self.get_conn().cursor() as cur:
            await cur.execute("SELECT * FROM assistant WHERE public = 1")
            rows = await cur.fetchall()
            return [_deserialize_assistant(row) for row in rows]

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
        updated_at = datetime.now(timezone.utc)
        conn = self.get_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO assistant (assistant_id, user_id, name, config, updated_at, public) 
                VALUES (?, ?, ?, ?, ?, ?) 
                ON CONFLICT(assistant_id) 
                DO UPDATE SET 
                    user_id = EXCLUDED.user_id, 
                    name = EXCLUDED.name, 
                    config = EXCLUDED.config, 
                    updated_at = EXCLUDED.updated_at, 
                    public = EXCLUDED.public
                """,
                (
                    assistant_id,
                    user_id,
                    name,
                    json.dumps(config),
                    updated_at.isoformat(),
                    public,
                ),
            )
            await conn.commit()
        return {
            "assistant_id": assistant_id,
            "user_id": user_id,
            "name": name,
            "config": config,
            "updated_at": updated_at,
            "public": public,
        }

    async def list_threads(self, user_id: str) -> list[Thread]:
        """List all threads for the current user."""
        async with self.get_conn().cursor() as cur:
            await cur.execute("SELECT * FROM thread WHERE user_id = ?", (user_id,))
            rows = await cur.fetchall()
            return [_deserialize_thread(row) for row in rows]

    async def get_thread(self, user_id: str, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        async with self.get_conn().cursor() as cur:
            await cur.execute(
                "SELECT * FROM thread WHERE thread_id = ? AND user_id = ?",
                (thread_id, user_id),
            )
            row = await cur.fetchone()
            return _deserialize_thread(row) if row else None

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
        return {"values": state.values, "next": state.next}

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
        conn = self.get_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO thread (thread_id, user_id, assistant_id, name, updated_at) 
                VALUES (?, ?, ?, ?, ?) 
                ON CONFLICT(thread_id) 
                DO UPDATE SET 
                    user_id = EXCLUDED.user_id,
                    assistant_id = EXCLUDED.assistant_id, 
                    name = EXCLUDED.name, 
                    updated_at = EXCLUDED.updated_at
                """,
                (thread_id, user_id, assistant_id, name, updated_at.isoformat()),
            )
            await conn.commit()
            return {
                "thread_id": thread_id,
                "user_id": user_id,
                "assistant_id": assistant_id,
                "name": name,
                "updated_at": updated_at,
            }

    async def get_or_create_user(self, sub: str) -> tuple[User, bool]:
        """Returns a tuple of the user and a boolean indicating whether the user was created."""
        conn = self.get_conn()
        async with conn.cursor() as cur:
            # Start a write transaction to avoid the unique contraint error due to
            # concurrent inserts.
            # TODO worked when connection wasn't shared across app
            await cur.execute("BEGIN EXCLUSIVE")
            await cur.execute('SELECT * FROM "user" WHERE sub = ?', (sub,))
            row = await cur.fetchone()
            if row:
                # Since we are using a single connection in the whole application,
                # we can't leave the transaction open, so we need to commit it here.
                await conn.commit()
                return _deserialize_user(row), False

            # SQLite doesn't support RETURNING *, so we need to manually fetch the created user.
            await cur.execute(
                'INSERT INTO "user" (user_id, sub, created_at) VALUES (?, ?, ?)',
                (str(uuid4()), sub, datetime.now(timezone.utc).isoformat()),
            )
            await conn.commit()

            await cur.execute('SELECT * FROM "user" WHERE sub = ?', (sub,))
            row = await cur.fetchone()
            return _deserialize_user(row), True

    async def delete_thread(self, user_id: str, thread_id: str) -> None:
        """Delete a thread by ID."""
        conn = self.get_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM thread WHERE thread_id = ? AND user_id = ?",
                (thread_id, user_id),
            )
            await conn.commit()


storage = SqliteStorage()

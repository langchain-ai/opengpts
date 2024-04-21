import json
from datetime import datetime, timezone
from typing import Any, Optional, Sequence, Union
from uuid import uuid4

from langchain_core.messages import AnyMessage

from app.agent import AgentType, get_agent_executor
from app.lifespan import sqlite_conn
from app.schema import Assistant, Thread, User
from app.storage.base import BaseStorage


class SqliteStorage(BaseStorage):
    async def list_assistants(self, user_id: str) -> list[Assistant]:
        """List all assistants for the current user."""
        async with sqlite_conn() as conn, conn.cursor() as cur:
            await cur.execute("SELECT * FROM assistant WHERE user_id = ?", (user_id,))
            rows = await cur.fetchall()

            # Deserialize the 'config' field from a JSON string to a dict for each row
            assistants = []
            for row in rows:
                assistant_data = dict(row)  # Convert sqlite3.Row to dict
                assistant_data["config"] = (
                    json.loads(assistant_data["config"])
                    if "config" in assistant_data and assistant_data["config"]
                    else {}
                )
                assistant = Assistant(**assistant_data)
                assistants.append(assistant)

            return assistants

    async def get_assistant(
        self, user_id: str, assistant_id: str
    ) -> Optional[Assistant]:
        """Get an assistant by ID."""
        async with sqlite_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT * FROM assistant WHERE assistant_id = ? AND (user_id = ? OR public = 1)",
                (assistant_id, user_id),
            )
            row = await cur.fetchone()
            if not row:
                return None
            assistant_data = dict(row)  # Convert sqlite3.Row to dict
            assistant_data["config"] = (
                json.loads(assistant_data["config"])
                if "config" in assistant_data and assistant_data["config"]
                else {}
            )
            return Assistant(**assistant_data)

    async def list_public_assistants(
        self, assistant_ids: Sequence[str]
    ) -> list[Assistant]:
        """List all the public assistants."""
        assistant_ids_tuple = tuple(
            assistant_ids
        )  # SQL requires a tuple for the IN operator.
        placeholders = ", ".join("?" for _ in assistant_ids)
        async with sqlite_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT * FROM assistant WHERE assistant_id IN ({placeholders}) AND public = 1",
                assistant_ids_tuple,
            )
            rows = await cur.fetchall()
            return [Assistant(**dict(row)) for row in rows]

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
        async with sqlite_conn() as conn, conn.cursor() as cur:
            # Convert the config dict to a JSON string for storage.
            config_str = json.dumps(config)
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
                    config_str,
                    updated_at.isoformat(),
                    public,
                ),
            )
            await conn.commit()
        return Assistant(
            assistant_id=assistant_id,
            user_id=user_id,
            name=name,
            config=config,
            updated_at=updated_at,
            public=public,
        )

    async def list_threads(self, user_id: str) -> list[Thread]:
        """List all threads for the current user."""
        async with sqlite_conn() as conn, conn.cursor() as cur:
            await cur.execute("SELECT * FROM thread WHERE user_id = ?", (user_id,))
            rows = await cur.fetchall()
            return [Thread(**dict(row)) for row in rows]

    async def get_thread(self, user_id: str, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        async with sqlite_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT * FROM thread WHERE thread_id = ? AND user_id = ?",
                (thread_id, user_id),
            )
            row = await cur.fetchone()
            return Thread(**dict(row)) if row else None

    async def get_thread_state(self, user_id: str, thread_id: str):
        """Get state for a thread."""
        app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
        state = await app.aget_state({"configurable": {"thread_id": thread_id}})
        return {
            "values": state.values,
            "next": state.next,
        }

    async def update_thread_state(
        self,
        user_id: str,
        thread_id: str,
        values: Union[Sequence[AnyMessage], dict[str, Any]],
    ):
        """Add state to a thread."""
        app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
        await app.aupdate_state({"configurable": {"thread_id": thread_id}}, values)

    async def get_thread_history(self, user_id: str, thread_id: str):
        """Get the history of a thread."""
        app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
        return [
            {
                "values": c.values,
                "next": c.next,
                "config": c.config,
                "parent": c.parent_config,
            }
            async for c in app.aget_state_history(
                {"configurable": {"thread_id": thread_id}}
            )
        ]

    async def put_thread(
        self, user_id: str, thread_id: str, *, assistant_id: str, name: str
    ) -> Thread:
        """Modify a thread."""
        updated_at = datetime.now(timezone.utc)
        async with sqlite_conn() as conn, conn.cursor() as cur:
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
                (thread_id, user_id, assistant_id, name, updated_at),
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
        async with sqlite_conn() as conn, conn.cursor() as cur:
            # start a write transaction to avoid the unique contraint error due to
            # concurrent inserts
            await cur.execute("BEGIN EXCLUSIVE")
            await cur.execute('SELECT * FROM "user" WHERE sub = ?', (sub,))
            user_row = await cur.fetchone()

            if user_row:
                # Convert sqlite3.Row to a User object
                user = User(
                    user_id=user_row["user_id"],
                    sub=user_row["sub"],
                    created_at=user_row["created_at"],
                )
                return user, False

            # SQLite doesn't support RETURNING *, so we need to manually fetch the created user.
            await cur.execute(
                'INSERT INTO "user" (user_id, sub, created_at) VALUES (?, ?, ?)',
                (str(uuid4()), sub, datetime.now()),
            )
            await conn.commit()

            # Fetch the newly created user
            await cur.execute('SELECT * FROM "user" WHERE sub = ?', (sub,))
            new_user_row = await cur.fetchone()

            new_user = User(
                user_id=new_user_row["user_id"],
                sub=new_user_row["sub"],
                created_at=new_user_row["created_at"],
            )
            return new_user, True

    async def delete_thread(self, user_id: str, thread_id: str) -> None:
        """Delete a thread by ID."""
        async with sqlite_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM thread WHERE thread_id = ? AND user_id = ?",
                (thread_id, user_id),
            )
            await conn.commit()


storage = SqliteStorage()

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import UUID, uuid4

from langchain_core.messages import AnyMessage

from app.agent import AgentType, get_agent_executor
from app.schema import Assistant, Thread, User


@contextmanager
def _connect():
    conn = sqlite3.connect("opengpts.db")
    conn.row_factory = sqlite3.Row  # Enable dictionary access to row items.
    try:
        yield conn
    finally:
        conn.close()


def list_assistants(user_id: str) -> List[Assistant]:
    """List all assistants for the current user."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assistant WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        return [Assistant(**dict(row)) for row in rows]


def get_assistant(user_id: str, assistant_id: str) -> Optional[Assistant]:
    """Get an assistant by ID."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM assistant WHERE assistant_id = ? AND (user_id = ? OR public = 1)",
            (assistant_id, user_id),
        )
        row = cursor.fetchone()
        return Assistant(**dict(row)) if row else None


async def list_public_assistants(assistant_ids: Sequence[str]) -> List[Assistant]:
    """List all the public assistants."""
    assistant_ids_tuple = tuple(
        assistant_ids
    )  # SQL requires a tuple for the IN operator.
    placeholders = ", ".join("?" for _ in assistant_ids)
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM assistant WHERE assistant_id IN ({placeholders}) AND public = 1",
            assistant_ids_tuple,
        )
        rows = cursor.fetchall()
        return [Assistant(**dict(row)) for row in rows]


async def put_assistant(
    user_id: str, assistant_id: str, *, name: str, config: dict, public: bool = False
) -> Assistant:
    """Modify an assistant."""
    updated_at = datetime.now(timezone.utc)
    with _connect() as conn:
        cursor = conn.cursor()
        # Convert the config dict to a JSON string for storage.
        config_str = json.dumps(config)
        cursor.execute(
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
            (assistant_id, user_id, name, config_str, updated_at.isoformat(), public),
        )
        conn.commit()
        return Assistant(
            assistant_id=UUID(assistant_id),
            user_id=user_id,
            name=name,
            config=config,
            updated_at=updated_at,
            public=public,
        )


async def list_threads(user_id: str) -> List[Thread]:
    """List all threads for the current user."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM thread WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        return [Thread(**dict(row)) for row in rows]


async def get_thread(user_id: str, thread_id: str) -> Optional[Thread]:
    """Get a thread by ID."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM thread WHERE thread_id = ? AND user_id = ?",
            (thread_id, user_id),
        )
        row = cursor.fetchone()
        return Thread(**dict(row)) if row else None


async def get_thread_state(user_id: str, thread_id: str):
    """Get state for a thread."""
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    state = await app.aget_state({"configurable": {"thread_id": thread_id}})
    return {
        "values": state.values,
        "next": state.next,
    }


async def update_thread_state(
    user_id: str, thread_id: str, values: Union[Sequence[AnyMessage], Dict[str, Any]]
):
    """Add state to a thread."""
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    await app.aupdate_state({"configurable": {"thread_id": thread_id}}, values)


async def get_thread_history(user_id: str, thread_id: str):
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


async def put_thread(user_id: str, thread_id: str, *, assistant_id: str, name: str) -> Thread:
    """Modify a thread."""
    updated_at = datetime.now(timezone.utc)
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
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
        return {
            "thread_id": thread_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
            "name": name,
            "updated_at": updated_at,
        }


def get_or_create_user(sub: str) -> tuple[User, bool]:
    """Returns a tuple of the user and a boolean indicating whether the user was created."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "user" WHERE sub = ?', (sub,))
        user_row = cursor.fetchone()

        if user_row:
            # Convert sqlite3.Row to a User object
            user = User(user_id=user_row["user_id"], sub=user_row["sub"], created_at=user_row["created_at"])
            return user, False

        # SQLite doesn't support RETURNING *, so we need to manually fetch the created user.
        cursor.execute('INSERT INTO "user" (user_id, sub, created_at) VALUES (?, ?, ?)', (str(uuid4()), sub, datetime.now()))
        conn.commit()

        # Fetch the newly created user
        cursor.execute('SELECT * FROM "user" WHERE sub = ?', (sub,))
        new_user_row = cursor.fetchone()

        new_user = User(user_id=new_user_row["user_id"], sub=new_user_row["sub"],
                            created_at=new_user_row["created_at"])
        return new_user, True


async def delete_thread(user_id: str, thread_id: str):
    """Delete a thread by ID."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM thread WHERE thread_id = ? AND user_id = ?",
            (thread_id, user_id),
        )
        conn.commit()
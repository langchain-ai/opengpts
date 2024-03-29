from datetime import datetime, timezone
from typing import List, Optional, Sequence
from fastapi import HTTPException, status
from langchain_core.messages import AnyMessage

from app.agent import AgentType, get_agent_executor
from app.lifespan import get_pg_pool
from app.schema import Assistant, Thread, User
from app.stream import map_chunk_to_msg


async def list_assistants(user_id: str) -> List[Assistant]:
    """List all assistants for the current user."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetch("SELECT * FROM assistant WHERE user_id = $1", user_id)


async def get_assistant(user_id: str, assistant_id: str) -> Optional[Assistant]:
    """Get an assistant by ID."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM assistant WHERE assistant_id = $1 AND (user_id = $2 OR public = true)",
            assistant_id,
            user_id,
        )


async def list_public_assistants(assistant_ids: Sequence[str]) -> List[Assistant]:
    """List all the public assistants."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetch(
            (
                "SELECT * FROM assistant "
                "WHERE assistant_id = ANY($1::uuid[]) "
                "AND public = true;"
            ),
            assistant_ids,
        )


async def put_assistant(
    user_id: str, assistant_id: str, *, name: str, config: dict, public: bool = False
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
    async with get_pg_pool().acquire() as conn:
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


async def list_threads(user_id: str) -> List[Thread]:
    """List all threads for the current user."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetch("SELECT * FROM thread WHERE user_id = $1", user_id)


async def get_thread(user_id: str, thread_id: str) -> Optional[Thread]:
    """Get a thread by ID."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM thread WHERE thread_id = $1 AND user_id = $2",
            thread_id,
            user_id,
        )


async def get_thread_messages(user_id: str, thread_id: str):
    """Get all messages for a thread."""
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    state = await app.aget_state({"configurable": {"thread_id": thread_id}})
    return {
        "messages": [map_chunk_to_msg(msg) for msg in state.values],
        "resumeable": bool(state.next),
    }


async def post_thread_messages(
    user_id: str, thread_id: str, messages: Sequence[AnyMessage]
):
    """Add messages to a thread."""
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    await app.aupdate_state({"configurable": {"thread_id": thread_id}}, messages)


async def get_thread_history(user_id: str, thread_id: str):
    """Get the history of a thread."""
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    return [
        {
            "values": [map_chunk_to_msg(msg) for msg in c.values],
            "resumeable": bool(c.next),
            "config": c.config,
            "parent": c.parent_config,
        }
        async for c in app.aget_state_history(
            {"configurable": {"thread_id": thread_id}}
        )
    ]


async def put_thread(
    user_id: str, thread_id: str, *, assistant_id: str, name: str
) -> Thread:
    """Modify a thread."""
    updated_at = datetime.now(timezone.utc)
    async with get_pg_pool().acquire() as conn:
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


async def get_user(user_id: str) -> Optional[User]:
    """Get a user by ID."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM \"user\" WHERE user_id = $1 AND is_deleted = FALSE",
            user_id,
        )


async def list_active_users() -> List[User]:
    """List all active users."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM \"user\" WHERE is_active = TRUE AND is_deleted = FALSE"
        )


async def register_user(
    username: str,
    password_hash: str,
    email: str,
    full_name: str,
    address: str,
    role: str
) -> User:
    """Register a new user."""
    creation_date = datetime.now(timezone.utc)
    last_login_date = None  # Assuming no login has occurred yet
    is_active = True
    
    async with get_pg_pool().acquire() as conn:
        try:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO \"user\" (username, password_hash, email, full_name, address, role, creation_date, last_login_date, is_active, is_deleted) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
                    username, password_hash, email, full_name, address, role,
                    creation_date, last_login_date, is_active, False
                )
                return User(
                    username=username,
                    password_hash=password_hash,
                    email=email,
                    full_name=full_name,
                    address=address,
                    role=role,
                    creation_date=creation_date,
                    last_login_date=last_login_date,
                    is_active=is_active
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register user {e}",
            )

async def login_user(
    username: str,
    password_hash: str
) -> Optional[User]:
    async with get_pg_pool().acquire() as conn:
        try:
            user_record = await conn.fetchrow(
                "SELECT * FROM \"user\" WHERE username = $1 AND password_hash = $2 AND is_deleted = FALSE",
                username, password_hash
            )
            
            if user_record is not None:
                last_login_date = datetime.now(timezone.utc)
                await conn.execute(
                    "UPDATE \"user\" SET last_login_date = $1 WHERE username = $2",
                    last_login_date, username
                )
                return User(
                    user_id=user_record['user_id'],
                    username=user_record['username'],
                    password_hash=user_record['password_hash'],
                    email=user_record['email'],
                    full_name=user_record['full_name'],
                    address=user_record['address'],
                    role=user_record['role'],
                    creation_date=user_record['creation_date'],
                    last_login_date=last_login_date,
                    is_active=user_record['is_active']
                )
            else:
                return None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to login user {e}",
            )


async def update_user(
    user_id: str,
    username: str,
    password_hash: str,
    email: str,
    full_name: str,
    address: str,
    role: str
) -> Optional[User]:
    """Update a user."""
    async with get_pg_pool().acquire() as conn:
        try:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE \"user\" SET username = $1, password_hash = $2, email = $3, full_name = $4, address = $5, role = $6 WHERE user_id = $7 AND is_deleted = FALSE",
                    username, password_hash, email, full_name, address, role, user_id
                )
                # Retrieve the updated user to return
                updated_user = await get_user(user_id)
                return updated_user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )

async def delete_user(user_id: str) -> bool:
    """Soft delete a user."""
    async with get_pg_pool().acquire() as conn:
        try:
            async with conn.transaction():
                result = await conn.execute(
                    "UPDATE \"user\" SET is_deleted = TRUE WHERE user_id = $1 AND is_deleted = FALSE",
                    user_id
                )
                # Check if a row was affected
                return result == 'UPDATE 1'
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

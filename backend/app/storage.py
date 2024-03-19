import datetime
from typing import List, Sequence

from langchain.schema.messages import AnyMessage
from langgraph.channels.base import ChannelsManager
from langgraph.checkpoint.base import empty_checkpoint
from langgraph.pregel import _prepare_next_tasks


from app.agent import AgentType, get_agent_executor
from app.schema import Assistant, Thread
from app.stream import map_chunk_to_msg
from app.lifespan import get_pg_pool


async def list_assistants(user_id: str) -> List[Assistant]:
    """List all assistants for the current user."""

    async with get_pg_pool().acquire() as conn:
        return await conn.fetch("SELECT * FROM assistant WHERE user_id = $1", user_id)


async def get_assistant(user_id: str, assistant_id: str) -> Assistant | None:
    """Get an assistant by ID."""

    async with get_pg_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM assistant WHERE assistant_id = $1 AND user_id = $2",
            assistant_id,
            user_id,
        )


async def get_public_assistant(assistant_id: str) -> Assistant | None:
    """Get a public assistant by ID."""

    async with get_pg_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM assistant WHERE assistant_id = $1 AND public = true",
            assistant_id,
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
    updated_at = datetime.datetime.now(datetime.UTC)
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


async def get_thread(user_id: str, thread_id: str) -> Thread | None:
    """Get a thread by ID."""
    async with get_pg_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM thread WHERE thread_id = $1 AND user_id = $2",
            thread_id,
            user_id,
        )


# TODO remove hardcoded channel name
MESSAGES_CHANNEL_NAME = "__root__"


async def get_thread_messages(user_id: str, thread_id: str):
    """Get all messages for a thread."""
    config = {"configurable": {"thread_id": thread_id}}
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    checkpoint = await app.checkpointer.aget(config) or empty_checkpoint()
    with ChannelsManager(app.channels, checkpoint) as channels:
        return {
            "messages": [
                map_chunk_to_msg(msg) for msg in channels[MESSAGES_CHANNEL_NAME].get()
            ],
            "resumeable": bool(_prepare_next_tasks(checkpoint, app.nodes, channels)),
        }


async def post_thread_messages(
    user_id: str, thread_id: str, messages: Sequence[AnyMessage]
):
    """Add messages to a thread."""
    config = {"configurable": {"thread_id": thread_id}}
    app = get_agent_executor([], AgentType.GPT_35_TURBO, "", False)
    checkpoint = await app.checkpointer.aget(config) or empty_checkpoint()
    with ChannelsManager(app.channels, checkpoint) as channels:
        channel = channels[MESSAGES_CHANNEL_NAME]
        channel.update([messages])
        checkpoint["channel_values"][MESSAGES_CHANNEL_NAME] = channel.checkpoint()
        checkpoint["channel_versions"][MESSAGES_CHANNEL_NAME] += 1
        await app.checkpointer.aput(config, checkpoint)


async def put_thread(
    user_id: str, thread_id: str, *, assistant_id: str, name: str
) -> Thread:
    """Modify a thread."""
    updated_at = datetime.datetime.now(datetime.UTC)
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

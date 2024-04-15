from contextlib import asynccontextmanager

from httpx import AsyncClient
from typing_extensions import AsyncGenerator


@asynccontextmanager
async def get_client() -> AsyncGenerator[AsyncClient, None]:
    """Get the app."""
    from app.server import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

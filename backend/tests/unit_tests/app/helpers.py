from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient
from typing_extensions import AsyncGenerator

from app.lifespan import lifespan


@asynccontextmanager
async def get_client() -> AsyncGenerator[AsyncClient, None]:
    """Get the app."""
    from app.server import app

    async with lifespan(app), AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as ac:
        yield ac

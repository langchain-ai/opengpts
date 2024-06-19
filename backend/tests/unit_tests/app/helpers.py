from contextlib import asynccontextmanager

from app.lifespan import lifespan
from httpx import AsyncClient, ASGITransport
from typing_extensions import AsyncGenerator


@asynccontextmanager
async def get_client() -> AsyncGenerator[AsyncClient, None]:
    """Get the app."""
    from app.server import app

    async with lifespan(app), AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as ac:
        yield ac

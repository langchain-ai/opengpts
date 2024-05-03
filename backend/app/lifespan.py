from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.storage.storage import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.setup()
    yield
    await storage.teardown()

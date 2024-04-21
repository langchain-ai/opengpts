from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite
import asyncpg
import orjson
from fastapi import FastAPI

from app.storage.settings import StorageType
from app.storage.settings import settings as storage_settings

_pg_pool = None
_global_sqlite_connections = []


async def create_sqlite_conn(global_: bool = False, **kwargs) -> aiosqlite.Connection:
    conn = await aiosqlite.connect("opengpts.db", **kwargs)
    conn.row_factory = aiosqlite.Row
    if global_:
        _global_sqlite_connections.append(conn)
    return conn


@asynccontextmanager
async def sqlite_conn(**kwargs) -> AsyncGenerator[aiosqlite.Connection, None]:
    conn = await create_sqlite_conn(**kwargs)
    try:
        yield conn
    finally:
        await conn.close()


async def _close_global_sqlite_connections() -> None:
    for conn in _global_sqlite_connections:
        await conn.close()
    _global_sqlite_connections.clear()


def get_pg_pool() -> asyncpg.pool.Pool:
    return _pg_pool


async def _init_connection(conn) -> None:
    await conn.set_type_codec(
        "json",
        encoder=lambda v: orjson.dumps(v).decode(),
        decoder=orjson.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "uuid", encoder=lambda v: str(v), decoder=lambda v: v, schema="pg_catalog"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if storage_settings.storage_type == StorageType.POSTGRES:
        global _pg_pool
        _pg_pool = await asyncpg.create_pool(
            database=storage_settings.postgres.db,
            user=storage_settings.postgres.user,
            password=storage_settings.postgres.password,
            host=storage_settings.postgres.host,
            port=storage_settings.postgres.port,
            init=_init_connection,
        )

    yield

    if storage_settings.storage_type == StorageType.POSTGRES:
        await _pg_pool.close()
        _pg_pool = None
    elif storage_settings.storage_type == StorageType.SQLITE:
        await _close_global_sqlite_connections()

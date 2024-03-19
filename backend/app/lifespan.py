import os
from contextlib import asynccontextmanager

import asyncpg
import orjson
from fastapi import FastAPI

_pg_pool = None


def get_pg_pool() -> asyncpg.pool.Pool:
    return _pg_pool


async def _init_connection(conn) -> None:
    await conn.set_type_codec(
        "json",
        encoder=lambda v: orjson.dumps(v).decode(),
        decoder=orjson.loads,
        schema="pg_catalog",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pg_pool

    _pg_pool = await asyncpg.create_pool(
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        init=_init_connection,
    )
    yield
    await _pg_pool.close()
    _pg_pool = None

from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI
import json
import os


_pg_pool = None


def get_pg_pool():
    return _pg_pool


async def _init_connection(conn):
    await conn.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
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

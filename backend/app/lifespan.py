import os
from contextlib import asynccontextmanager

import asyncpg
import orjson
import structlog
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
    await conn.set_type_codec(
        "jsonb",
        encoder=lambda v: orjson.dumps(v).decode(),
        decoder=orjson.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "uuid", encoder=lambda v: str(v), decoder=lambda v: v, schema="pg_catalog"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

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

import asyncio
import os
import subprocess

import asyncpg
import pytest

from app.auth.settings import AuthType
from app.auth.settings import settings as auth_settings
from app.lifespan import get_pg_pool, lifespan
from app.server import app

auth_settings.auth_type = AuthType.NOOP

# Temporary handling of environment variables for testing
os.environ["OPENAI_API_KEY"] = "test"

TEST_DB = "test"
assert os.environ["POSTGRES_DB"] != TEST_DB, "Test and main database conflict."
os.environ["POSTGRES_DB"] = TEST_DB


async def _get_conn() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        database="postgres",
    )


async def _create_test_db() -> None:
    """Check if the test database exists and create it if it doesn't."""
    conn = await _get_conn()
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", TEST_DB)
    if not exists:
        await conn.execute(f'CREATE DATABASE "{TEST_DB}"')
    await conn.close()


async def _drop_test_db() -> None:
    """Check if the test database exists and if so, drop it."""
    conn = await _get_conn()
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", TEST_DB)
    if exists:
        await conn.execute(f'DROP DATABASE "{TEST_DB}" WITH (FORCE)')
    await conn.close()


def _migrate_test_db() -> None:
    subprocess.run(["make", "migrate"], check=True)


@pytest.fixture(scope="session")
async def pool():
    await _drop_test_db()  # In case previous test session was abruptly terminated
    await _create_test_db()
    _migrate_test_db()
    async with lifespan(app):
        yield get_pg_pool()
    await _drop_test_db()


@pytest.fixture(scope="function", autouse=True)
async def clear_test_db(pool):
    """Truncate all tables before each test."""
    async with pool.acquire() as conn:
        query = """
        DO
        $$
        DECLARE
        r RECORD;
        BEGIN
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
            EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE;';
        END LOOP;
        END
        $$;
        """
        await conn.execute(query)


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

"""Shared fixtures for scraper integration tests.

Tests run against the Supabase database (DATABASE_URL env var). The clean_queue
fixture deletes test rows before and after each test to avoid interference.
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest_asyncio
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

# Load .env from project root (one level up from scraper/)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest_asyncio.fixture(scope="session")
async def pool():
    """Session-scoped connection pool using DATABASE_URL (Supabase)."""
    p = AsyncConnectionPool(
        os.environ["DATABASE_URL"],
        open=False,
        kwargs={"prepare_threshold": None},
    )
    await p.open()
    yield p
    await p.close()


@pytest_asyncio.fixture(scope="session")
async def university_id(pool):
    """Return the UUID of the 'monash' university row (seeded in migrations)."""
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT id FROM universities WHERE slug = 'monash'")
            row = await cur.fetchone()
    assert row is not None, "monash university not seeded — run migrations first"
    return str(row["id"])


@pytest_asyncio.fixture(autouse=True)
async def clean_queue(pool, university_id):
    """Delete scrape_runs and scrape_queue rows for monash before and after each test."""
    async with pool.connection() as conn:
        await conn.execute(
            "DELETE FROM scrape_queue WHERE university_id = %s", (university_id,)
        )
        await conn.execute(
            "DELETE FROM scrape_runs WHERE university_id = %s", (university_id,)
        )
    yield
    async with pool.connection() as conn:
        await conn.execute(
            "DELETE FROM scrape_queue WHERE university_id = %s", (university_id,)
        )
        await conn.execute(
            "DELETE FROM scrape_runs WHERE university_id = %s", (university_id,)
        )

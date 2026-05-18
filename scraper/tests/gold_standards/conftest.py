"""
Conftest for gold-standard fixture tests.

Overrides the parent conftest's pool, university_id, and clean_queue fixtures
so these tests run with no database connection and no network access.
"""
import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope="session")
async def pool():
    """No-op override. Gold-standard tests require no DB connection."""
    return None


@pytest_asyncio.fixture(scope="session")
async def university_id(pool):
    """No-op override. Gold-standard tests derive university IDs from UNI_MAP."""
    return None


@pytest_asyncio.fixture(autouse=True)
async def clean_queue(pool, university_id):
    """No-op override. Gold-standard tests write no DB rows."""
    yield

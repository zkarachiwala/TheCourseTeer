# Scraper Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a durable URL queue to the scraper so runs are resumable after interruption, with per-URL retry tracking and a per-university run sequence number.

**Architecture:** A `scrape_runs` table tracks each scrape attempt per university (with a sequence number and discovery flag); a `scrape_queue` table stores every discovered URL with status, attempt count, and error. `BaseScraper.run()` owns queue orchestration — subclasses implement `discover_urls` and `scrape_url` (or override `_process_batch` for browser-based scrapers that need a shared context).

**Tech Stack:** Python 3.12, psycopg3 (async), psycopg-pool, Playwright (Monash), httpx (RMIT), dbmate migrations, pytest + pytest-asyncio (integration tests against local Postgres on port 5433).

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `db/migrations/20260416000001_create_scrape_queue.sql` | Schema for `scrape_runs` and `scrape_queue` |
| Modify | `scraper/pyproject.toml` | Add pytest, pytest-asyncio |
| Create | `scraper/tests/__init__.py` | Empty, marks test package |
| Create | `scraper/tests/conftest.py` | DB pool fixture (local dev DB) |
| Create | `scraper/tests/test_queue_db.py` | Integration tests for queue db functions |
| Modify | `scraper/db.py` | Add queue functions; remove `get_existing_source_urls` |
| Modify | `scraper/base_scraper.py` | New interface: `discover_urls`, `scrape_url`, `_process_batch`; queue orchestration in `run()` |
| Modify | `scraper/monash.py` | Implement `discover_urls`; override `_process_batch`; add stub `scrape_url` |
| Modify | `scraper/rmit.py` | Implement `discover_urls`; override `_process_batch`; implement `scrape_url` |
| Modify | `scraper/run.py` | Add `--force` and `--university` CLI flags |

---

## Task 1: Database migration

**Files:**
- Create: `db/migrations/20260416000001_create_scrape_queue.sql`

- [ ] **Step 1: Write the migration**

```sql
-- migrate:up
CREATE TABLE scrape_runs (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id       uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    run_number          int         NOT NULL,
    discovery_complete  boolean     NOT NULL DEFAULT false,
    status              text        NOT NULL DEFAULT 'in_progress',
    forced              boolean     NOT NULL DEFAULT false,
    started_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz,
    UNIQUE (university_id, run_number)
);

CREATE INDEX scrape_runs_university_status_idx
    ON scrape_runs(university_id, status);

CREATE TABLE scrape_queue (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id       uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    discovered_run_id   uuid        NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
    completed_run_id    uuid        REFERENCES scrape_runs(id) ON DELETE SET NULL,
    url                 text        NOT NULL,
    status              text        NOT NULL DEFAULT 'pending',
    attempt_count       int         NOT NULL DEFAULT 0,
    last_error          text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (university_id, url)
);

CREATE INDEX scrape_queue_university_status_idx
    ON scrape_queue(university_id, status);

CREATE OR REPLACE TRIGGER scrape_queue_set_updated_at
    BEFORE UPDATE ON scrape_queue
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- migrate:down
DROP TRIGGER scrape_queue_set_updated_at ON scrape_queue;
DROP TABLE scrape_queue;
DROP TABLE scrape_runs;
```

- [ ] **Step 2: Run the migration (DATABASE_URL env var points to Supabase)**

From the project root:
```bash
bash scripts/migrate.sh
```

Expected output: `Applying: 20260416000001_create_scrape_queue.sql`

- [ ] **Step 3: Verify tables exist**

```bash
bash scripts/psql.sh -c "\dt scrape_*"
```

Expected: two rows — `scrape_queue` and `scrape_runs`.

- [ ] **Step 4: Commit**

```bash
git add db/migrations/20260416000001_create_scrape_queue.sql
git commit -m "feat: add scrape_runs and scrape_queue tables"
```

---

## Task 2: Add pytest and test fixtures

**Files:**
- Modify: `scraper/pyproject.toml`
- Create: `scraper/tests/__init__.py`
- Create: `scraper/tests/conftest.py`

- [ ] **Step 1: Add test dependencies**

In `scraper/pyproject.toml`, add to the `dependencies` list:
```toml
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
```

Then install:
```bash
cd scraper && uv sync
```

- [ ] **Step 2: Create `scraper/tests/__init__.py`**

Empty file:
```python
```

- [ ] **Step 3: Create `scraper/tests/conftest.py`**

```python
"""Shared fixtures for scraper integration tests.

Tests run against the Supabase database (DATABASE_URL env var). The clean_queue
fixture deletes test rows before and after each test to avoid interference.
"""
import asyncio
import os

import pytest
import pytest_asyncio
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


@pytest.fixture(scope="session")
def event_loop_policy():
    # psycopg3 requires SelectorEventLoop on Windows
    return asyncio.DefaultEventLoopPolicy()


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


@pytest_asyncio.fixture
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
```

- [ ] **Step 4: Add pytest config to `scraper/pyproject.toml`**

Append after the `[tool.uv]` section:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: Verify pytest runs (no tests yet)**

```bash
cd scraper && uv run pytest -v
```

Expected: `no tests ran` or `0 passed`.

- [ ] **Step 6: Commit**

```bash
git add scraper/pyproject.toml scraper/tests/
git commit -m "feat: add pytest and DB test fixtures"
```

---

## Task 3: Queue functions in db.py

**Files:**
- Create: `scraper/tests/test_queue_db.py`
- Modify: `scraper/db.py`

- [ ] **Step 1: Write failing tests**

Create `scraper/tests/test_queue_db.py`:

```python
"""Integration tests for scrape queue DB functions."""
import pytest
from db import (
    complete_run,
    enqueue_urls,
    get_or_create_run,
    get_pending_urls,
    mark_discovery_complete,
    mark_url_complete,
    mark_url_failed,
)


async def test_get_or_create_run_creates_first_run(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    assert run["run_number"] == 1
    assert run["status"] == "in_progress"
    assert run["discovery_complete"] is False
    assert run["forced"] is False


async def test_get_or_create_run_resumes_existing(pool, university_id):
    run1 = await get_or_create_run(pool, university_id, force=False)
    run2 = await get_or_create_run(pool, university_id, force=False)
    assert run1["id"] == run2["id"]


async def test_get_or_create_run_increments_on_force(pool, university_id):
    await get_or_create_run(pool, university_id, force=False)
    run2 = await get_or_create_run(pool, university_id, force=True)
    assert run2["run_number"] == 2
    assert run2["forced"] is True


async def test_force_deletes_queue_rows(pool, university_id):
    run1 = await get_or_create_run(pool, university_id, force=False)
    await enqueue_urls(pool, university_id, str(run1["id"]), ["https://example.com/a"])
    run2 = await get_or_create_run(pool, university_id, force=True)
    pending = await get_pending_urls(pool, university_id)
    assert pending == []


async def test_enqueue_urls_inserts_pending(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    urls = ["https://example.com/a", "https://example.com/b"]
    await enqueue_urls(pool, university_id, str(run["id"]), urls)
    pending = await get_pending_urls(pool, university_id)
    assert set(pending) == set(urls)


async def test_enqueue_urls_is_idempotent(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    url = "https://example.com/a"
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    pending = await get_pending_urls(pool, university_id)
    assert pending.count(url) == 1


async def test_mark_url_complete_removes_from_pending(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    run_id = str(run["id"])
    await enqueue_urls(pool, university_id, run_id, ["https://example.com/a"])
    await mark_url_complete(pool, university_id, "https://example.com/a", run_id)
    pending = await get_pending_urls(pool, university_id)
    assert pending == []


async def test_mark_url_failed_increments_attempt(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    url = "https://example.com/a"
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    await mark_url_failed(pool, university_id, url, "timeout")
    # Still pending (attempt_count=1 < max_attempts=3)
    pending = await get_pending_urls(pool, university_id, max_attempts=3)
    assert url in pending


async def test_mark_url_failed_three_times_marks_failed(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    url = "https://example.com/a"
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    for _ in range(3):
        await mark_url_failed(pool, university_id, url, "timeout", max_attempts=3)
    pending = await get_pending_urls(pool, university_id, max_attempts=3)
    assert url not in pending


async def test_complete_run_sets_status(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    await complete_run(pool, str(run["id"]))
    # A new call without force should create a new run (old one is complete)
    run2 = await get_or_create_run(pool, university_id, force=False)
    assert run2["id"] != run["id"]
    assert run2["run_number"] == 2
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd scraper && uv run pytest tests/test_queue_db.py -v
```

Expected: `ImportError` — queue functions don't exist yet.

- [ ] **Step 3: Add queue functions to `scraper/db.py`**

Add these imports at the top of `db.py` (after existing imports):
```python
from psycopg.rows import dict_row
```
(already imported — confirm it's present, do not duplicate)

Add these functions at the end of `db.py`, before the closing:

```python
async def get_or_create_run(
    pool: AsyncConnectionPool, university_id: str, force: bool = False
) -> dict:
    """Return the current in_progress run, or create a new one.

    If force=True, delete all scrape_queue rows for this university first,
    then always create a new run.
    """
    async with pool.connection() as conn:
        if force:
            await conn.execute(
                "DELETE FROM scrape_queue WHERE university_id = %s", (university_id,)
            )
        else:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT * FROM scrape_runs
                    WHERE university_id = %s AND status = 'in_progress'
                    ORDER BY run_number DESC LIMIT 1
                    """,
                    (university_id,),
                )
                row = await cur.fetchone()
            if row:
                return dict(row)

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO scrape_runs (university_id, run_number, forced)
                SELECT %s, COALESCE(MAX(run_number), 0) + 1, %s
                FROM scrape_runs WHERE university_id = %s
                RETURNING *
                """,
                (university_id, force, university_id),
            )
            return dict(await cur.fetchone())


async def mark_discovery_complete(pool: AsyncConnectionPool, run_id: str) -> None:
    """Mark discovery as complete for this run."""
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE scrape_runs SET discovery_complete = true WHERE id = %s",
            (run_id,),
        )


async def enqueue_urls(
    pool: AsyncConnectionPool, university_id: str, run_id: str, urls: list[str]
) -> None:
    """Insert URLs as pending queue entries. Skips duplicates (ON CONFLICT DO NOTHING)."""
    if not urls:
        return
    async with pool.connection() as conn:
        await conn.executemany(
            """
            INSERT INTO scrape_queue (university_id, discovered_run_id, url)
            VALUES (%s, %s, %s)
            ON CONFLICT (university_id, url) DO NOTHING
            """,
            [(university_id, run_id, url) for url in urls],
        )


async def get_pending_urls(
    pool: AsyncConnectionPool, university_id: str, max_attempts: int = 3
) -> list[str]:
    """Return pending URLs for this university where attempt_count < max_attempts."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT url FROM scrape_queue
                WHERE university_id = %s
                  AND status = 'pending'
                  AND attempt_count < %s
                ORDER BY created_at
                """,
                (university_id, max_attempts),
            )
            rows = await cur.fetchall()
    return [row[0] for row in rows]


async def mark_url_complete(
    pool: AsyncConnectionPool, university_id: str, url: str, run_id: str
) -> None:
    """Mark a queue entry as complete."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE scrape_queue
            SET status = 'complete', completed_run_id = %s
            WHERE university_id = %s AND url = %s
            """,
            (run_id, university_id, url),
        )


async def mark_url_failed(
    pool: AsyncConnectionPool,
    university_id: str,
    url: str,
    error: str,
    max_attempts: int = 3,
) -> None:
    """Increment attempt count; set status='failed' once max_attempts is reached."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE scrape_queue
            SET attempt_count = attempt_count + 1,
                last_error = %s,
                status = CASE WHEN attempt_count + 1 >= %s THEN 'failed' ELSE 'pending' END
            WHERE university_id = %s AND url = %s
            """,
            (error, max_attempts, university_id, url),
        )


async def complete_run(pool: AsyncConnectionPool, run_id: str) -> None:
    """Mark a run as complete."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE scrape_runs
            SET status = 'complete', completed_at = now()
            WHERE id = %s
            """,
            (run_id,),
        )
```

Also remove `get_existing_source_urls` from `db.py` (it is replaced by the queue).

- [ ] **Step 4: Run tests — expect pass**

```bash
cd scraper && uv run pytest tests/test_queue_db.py -v
```

Expected: all 11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scraper/db.py scraper/tests/test_queue_db.py
git commit -m "feat: add scrape queue functions to db.py"
```

---

## Task 4: Update BaseScraper

**Files:**
- Modify: `scraper/base_scraper.py`

- [ ] **Step 1: Replace `scraper/base_scraper.py` entirely**

```python
"""Base class for all university course scrapers."""
import asyncio
import urllib.robotparser
from abc import ABC, abstractmethod

from psycopg_pool import AsyncConnectionPool

from db import (
    complete_run,
    enqueue_urls,
    get_or_create_run,
    get_pending_urls,
    get_university,
    mark_discovery_complete,
    mark_url_complete,
    mark_url_failed,
    update_university_status,
    upsert_course,
)
from http_client import make_client
from models import CourseData
from robots import fetch_and_store_robots, is_allowed

MAX_ATTEMPTS = 3


class BaseScraper(ABC):
    """
    Base class for all university course scrapers.

    Subclasses must implement:
    - discover_urls(rp) -> list[str]: fetch the listing page and return course URLs.
    - scrape_url(rp, url) -> CourseData | None: fetch and parse one course page.
      (Browser-based scrapers may instead override _process_batch for shared context.)

    run() handles queue orchestration, retries, and status updates.
    Pass force=True to reset the queue and re-run discovery from scratch.
    """

    _CONCURRENCY: int = 5

    def __init__(self, pool: AsyncConnectionPool, university_slug: str) -> None:
        self.pool = pool
        self.slug = university_slug
        self._university: dict | None = None

    async def run(self, force: bool = False) -> int:
        """Run the scraper with queue-based resume support. Returns count of upserted courses."""
        self._university = await get_university(self.pool, self.slug)
        university_id = self.university_id

        async with make_client() as client:
            rp = await fetch_and_store_robots(
                self.pool, university_id, self._university["homepage_url"], client
            )

        try:
            scrape_run = await get_or_create_run(self.pool, university_id, force)
            run_id = str(scrape_run["id"])

            if not scrape_run["discovery_complete"]:
                urls = await self.discover_urls(rp)
                await enqueue_urls(self.pool, university_id, run_id, urls)
                await mark_discovery_complete(self.pool, run_id)
                print(f"  {self.slug}: {len(urls)} URLs discovered (run #{scrape_run['run_number']})")

            pending = await get_pending_urls(self.pool, university_id, MAX_ATTEMPTS)
            print(f"  {self.slug}: {len(pending)} pending URLs")

            pairs = await self._process_batch(rp, pending)

            completed = 0
            for url, result in pairs:
                if isinstance(result, PermissionError):
                    await update_university_status(self.pool, university_id, "robots_blocked")
                    raise result
                elif isinstance(result, Exception):
                    await mark_url_failed(self.pool, university_id, url, str(result), MAX_ATTEMPTS)
                elif result is not None:
                    await upsert_course(self.pool, result)
                    await mark_url_complete(self.pool, university_id, url, run_id)
                    completed += 1
                else:
                    await mark_url_complete(self.pool, university_id, url, run_id)

            await complete_run(self.pool, run_id)
            await update_university_status(self.pool, university_id, "last_ok")
            return completed

        except PermissionError:
            await update_university_status(self.pool, university_id, "robots_blocked")
            raise
        except Exception:
            await update_university_status(self.pool, university_id, "failing")
            raise

    async def _process_batch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        urls: list[str],
    ) -> list[tuple[str, CourseData | Exception | None]]:
        """Scrape a batch of URLs concurrently. Override for browser-based scrapers."""
        sem = asyncio.Semaphore(self._CONCURRENCY)
        tasks = [self._safe_scrape(rp, url, sem) for url in urls]
        return list(await asyncio.gather(*tasks))

    async def _safe_scrape(
        self,
        rp: urllib.robotparser.RobotFileParser,
        url: str,
        sem: asyncio.Semaphore,
    ) -> tuple[str, CourseData | Exception | None]:
        async with sem:
            try:
                return url, await self.scrape_url(rp, url)
            except Exception as e:
                return url, e

    @property
    def university_id(self) -> str:
        """UUID of the current university. Available after run() starts."""
        if self._university is None:
            raise RuntimeError("university_id accessed before run()")
        return str(self._university["id"])

    def check_robots(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> None:
        """Raise PermissionError if url is disallowed by robots.txt."""
        if not is_allowed(rp, url):
            raise PermissionError(f"robots.txt blocks {url}")

    @abstractmethod
    async def discover_urls(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[str]:
        """Return all course URLs from the university listing page."""
        ...

    @abstractmethod
    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        """Fetch and parse one course page. Return None if the page is not a valid course."""
        ...
```

- [ ] **Step 2: Verify no import errors**

```bash
cd scraper && uv run python -c "from base_scraper import BaseScraper; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add scraper/base_scraper.py
git commit -m "feat: refactor BaseScraper with queue orchestration and discover_urls/scrape_url interface"
```

---

## Task 5: Update monash.py

**Files:**
- Modify: `scraper/monash.py`

- [ ] **Step 1: Replace `scraper/monash.py` entirely**

```python
"""Monash University course scraper (Playwright — required for Cloudflare bypass).

On Windows, psycopg3 requires SelectorEventLoop while Playwright requires
ProactorEventLoop (to spawn subprocesses). This is resolved by running all
Playwright work inside a thread-pool executor via asyncio.run(), which creates
its own ProactorEventLoop. DB operations stay on the main SelectorEventLoop.
"""
import asyncio
import concurrent.futures
import json
import re
import urllib.robotparser
from collections.abc import Callable

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from base_scraper import BaseScraper
from browser import browser_context
from db import get_campus_map
from models import CourseData

LISTING_URL = "https://www.monash.edu/study/courses/find-a-course"
_BASE_URL = "https://www.monash.edu"
# Degree course codes: single letter + 4 digits (e.g. b2029, m6014, a6013).
# Excludes professional-development codes like pdm1176, pdd1092.
_DEGREE_CODE_RE = re.compile(r"-[a-z]\d{4}$")
_CONCURRENCY = 3


class MonashScraper(BaseScraper):
    """Scraper for Monash University. Uses Playwright to bypass Cloudflare."""

    _CONCURRENCY = _CONCURRENCY

    async def discover_urls(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[str]:
        """Fetch the listing page via Playwright and return all degree-course URLs."""
        loop = asyncio.get_running_loop()
        check_robots = self.check_robots
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return await loop.run_in_executor(
                ex,
                lambda: asyncio.run(_playwright_discover(rp, check_robots)),
            )

    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        # Not used directly — _process_batch handles all Playwright fetching
        # in a single browser session. This satisfies the abstract method requirement.
        raise NotImplementedError("MonashScraper fetches via _process_batch")

    async def _process_batch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        urls: list[str],
    ) -> list[tuple[str, CourseData | Exception | None]]:
        """Run all URL fetches in one Playwright browser session (thread executor)."""
        if not urls:
            return []
        campus_map = await get_campus_map(self.pool, self.university_id)
        loop = asyncio.get_running_loop()
        check_robots = self.check_robots
        university_id = self.university_id
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return await loop.run_in_executor(
                ex,
                lambda: asyncio.run(
                    _playwright_fetch_batch(rp, check_robots, urls, university_id, campus_map)
                ),
            )


async def _playwright_discover(
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
) -> list[str]:
    """Run inside asyncio.run() in a thread. Fetches listing page, returns course URLs."""
    async with browser_context() as ctx:
        check_robots(rp, LISTING_URL)
        page = await ctx.new_page()
        try:
            await page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=30000)
            html = await page.content()
        finally:
            await page.close()

    seen: set[str] = set()
    for m in re.finditer(
        r'https://www\.monash\.edu(/study/courses/find-a-course/[^\s"<>&?]+)', html
    ):
        path = m.group(1)
        slug = path.split("/")[-1]
        if _DEGREE_CODE_RE.search(slug):
            seen.add(_BASE_URL + path)
    return list(seen)


async def _playwright_fetch_batch(
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
    urls: list[str],
    university_id: str,
    campus_map: dict[str, str],
) -> list[tuple[str, CourseData | Exception | None]]:
    """Run inside asyncio.run() in a thread. Fetches all URLs, returns (url, result) pairs."""
    async with browser_context() as ctx:
        sem = asyncio.Semaphore(_CONCURRENCY)
        tasks = [_fetch_one(ctx, rp, check_robots, url, university_id, campus_map, sem) for url in urls]
        return list(await asyncio.gather(*tasks))


async def _fetch_one(
    ctx: BrowserContext,
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
    url: str,
    university_id: str,
    campus_map: dict[str, str],
    sem: asyncio.Semaphore,
) -> tuple[str, CourseData | Exception | None]:
    check_robots(rp, url)
    async with sem:
        await asyncio.sleep(2)
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            html = await page.content()
        except Exception as e:
            return url, e
        finally:
            await page.close()
    return url, _parse_course(html, url, university_id, campus_map)


def _parse_course(
    html: str,
    url: str,
    university_id: str,
    campus_map: dict[str, str],
) -> CourseData | None:
    """Parse a course page into a CourseData record."""
    soup = BeautifulSoup(html, "lxml")
    name = _parse_name(soup, html)
    if not name:
        return None

    table = _parse_info_table(soup)
    qualification = table.get("Qualification", "")
    degree_type = _parse_degree_type(qualification)
    if degree_type is None:
        m = re.search(r"-([a-z])\d{4}$", url)
        if m:
            degree_type = "UG" if m.group(1) == "b" else "PG"
    campus_id = _resolve_campus(table.get("Location", ""), campus_map)
    duration = _parse_duration(table.get("Duration", ""))
    csp_fee, dfee = _parse_fees(html)
    atar_rank, atar_guaranteed = _parse_atar(soup)

    return CourseData(
        university_id=university_id,
        name=name,
        source_url=url,
        faculty=None,
        campus_id=campus_id,
        degree_type=degree_type,
        duration_years=duration,
        price_annual_csp_aud=csp_fee,
        price_annual_dfee_aud=dfee,
        csp_available=csp_fee is not None,
        atar_lowest_selection_rank=atar_rank,
        atar_guaranteed=atar_guaranteed,
    )


def _parse_name(soup: BeautifulSoup, html: str) -> str | None:
    """Return course name from JSON-LD Course block, falling back to H1."""
    for m in re.finditer(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    ):
        try:
            data = json.loads(m.group(1))
            if data.get("@type") == "Course" and data.get("name"):
                return data["name"]
        except (json.JSONDecodeError, AttributeError):
            pass
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else None


def _parse_info_table(soup: BeautifulSoup) -> dict[str, str]:
    """Return key->value pairs from the course-page__table-basic table."""
    table = soup.find("table", class_="course-page__table-basic")
    if not table:
        return {}
    result: dict[str, str] = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).rstrip(":")
            value = cells[1].get_text(" ", strip=True)
            result[key] = value
    return result


def _parse_degree_type(qualification: str) -> str | None:
    """Infer UG/PG from qualification string."""
    q = qualification.lower()
    if "bachelor" in q:
        return "UG"
    if any(k in q for k in ("master", "graduate", "doctor", "phd")):
        return "PG"
    return None


def _resolve_campus(location: str, campus_map: dict[str, str]) -> str | None:
    """Extract campus name from location string and resolve to a DB uuid."""
    m = re.search(r"on.campus at ([^:,]+)", location, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).strip()
    for name, campus_id in campus_map.items():
        if raw.lower() == name.lower():
            return campus_id
    return None


def _parse_duration(text: str) -> float | None:
    """Parse 'X years (full time)' -> X, or first year value if no qualifier."""
    m = re.search(r"(\d+(?:\.\d+)?)\s+years?\s*\(full.?time\)", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s+years?", text, re.IGNORECASE)
    return float(m.group(1)) if m else None


def _parse_fees(html: str) -> tuple[int | None, int | None]:
    """Extract CSP and full-fee domestic amounts from the inline JS data layer."""
    csp = None
    dfee = None
    m = re.search(r'"FeeDomesticCSP":\s*"A\$([0-9,]+)"', html)
    if m:
        csp = int(m.group(1).replace(",", ""))
    m = re.search(r'"FeeDomesticFullFee":\s*"A\$([0-9,]+)"', html)
    if m:
        dfee = int(m.group(1).replace(",", ""))
    return csp, dfee


def _parse_atar(soup: BeautifulSoup) -> tuple[int | None, int | None]:
    """
    Return (atar_lowest_selection_rank, atar_guaranteed) from course-page__subject-req-item
    elements. Values are integers (fractional parts truncated).
    """
    atar_rank: int | None = None
    atar_guaranteed: int | None = None
    for div in soup.find_all("div", class_="course-page__subject-req-item"):
        h2 = div.find("h2")
        if not h2:
            continue
        try:
            val = int(float(h2.get_text(strip=True)))
        except ValueError:
            continue
        label = div.get_text(" ", strip=True).lower()
        if "lowest selection rank" in label:
            atar_rank = val
        elif "guarantee" in label:
            atar_guaranteed = val
    return atar_rank, atar_guaranteed
```

- [ ] **Step 2: Verify no import errors**

```bash
cd scraper && uv run python -c "from monash import MonashScraper; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add scraper/monash.py
git commit -m "feat: refactor MonashScraper to discover_urls / _process_batch interface"
```

---

## Task 6: Update rmit.py

**Files:**
- Modify: `scraper/rmit.py`

- [ ] **Step 1: Replace `scraper/rmit.py` entirely**

```python
"""RMIT University course scraper (static / httpx)."""
import asyncio
import re
import urllib.robotparser

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from db import get_campus_id
from http_client import make_client
from models import CourseData

SITEMAP_URL = "https://www.rmit.edu.au/sitemap.xml"
_UG_PREFIX = "/study-with-us/levels-of-study/undergraduate-study/"
# Root course URLs split to exactly 8 segments.
_COURSE_DEPTH = 8
_CONCURRENCY = 5


class RmitScraper(BaseScraper):
    """Scraper for RMIT University. Discovers courses from sitemap.xml."""

    _CONCURRENCY = _CONCURRENCY

    async def discover_urls(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[str]:
        """Fetch sitemap.xml and return root-level UG course URLs."""
        async with make_client() as client:
            resp = await client.get(SITEMAP_URL)
            resp.raise_for_status()
        return [
            m.group(1)
            for m in re.finditer(r"<loc>(https://[^<]+)</loc>", resp.text)
            if _UG_PREFIX in m.group(1) and len(m.group(1).split("/")) == _COURSE_DEPTH
        ]

    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        """Fetch and parse one RMIT course page."""
        self.check_robots(rp, url)
        async with make_client() as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            print(f"  rmit: {resp.status_code} {url}")
            return None
        return await self._parse(url, resp.text)

    async def _process_batch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        urls: list[str],
    ) -> list[tuple[str, CourseData | Exception | None]]:
        """Override to share one httpx client across all concurrent requests."""
        if not urls:
            return []
        campus_id = await get_campus_id(self.pool, self.university_id, "rmit-city")
        sem = asyncio.Semaphore(self._CONCURRENCY)
        async with make_client() as client:
            tasks = [
                self._safe_fetch(rp, url, client, campus_id, sem) for url in urls
            ]
            return list(await asyncio.gather(*tasks))

    async def _safe_fetch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        url: str,
        client,
        campus_id: str | None,
        sem: asyncio.Semaphore,
    ) -> tuple[str, CourseData | Exception | None]:
        self.check_robots(rp, url)
        try:
            async with sem:
                resp = await client.get(url)
            if resp.status_code != 200:
                print(f"  rmit: {resp.status_code} {url}")
                return url, None
            return url, await self._parse(url, resp.text, campus_id)
        except Exception as e:
            return url, e

    async def _parse(
        self,
        url: str,
        html: str,
        campus_id: str | None = None,
    ) -> CourseData | None:
        meta = _parse_meta(html)
        name = meta.get("product_name")
        if not name:
            return None
        mode = meta.get("learning_mode_domestic", "")
        effective_campus_id = None if "online" in mode.lower() else campus_id
        atar_rank, atar_guaranteed = _parse_atar(meta.get("atar"))
        return CourseData(
            university_id=self.university_id,
            name=name,
            source_url=url,
            faculty=meta.get("college") or None,
            campus_id=effective_campus_id,
            degree_type="UG",
            duration_years=_parse_duration(meta.get("duration_domestic")),
            csp_available=_parse_csp(meta.get("fees_domestic")),
            price_annual_csp_aud=None,
            price_annual_dfee_aud=None,
            atar_lowest_selection_rank=atar_rank,
            atar_guaranteed=atar_guaranteed,
        )


def _parse_meta(html: str) -> dict[str, str]:
    """Extract all <meta class="elastic"> tags into a name->content dict."""
    soup = BeautifulSoup(html, "lxml")
    return {
        tag["name"]: tag.get("content", "")
        for tag in soup.find_all("meta", class_="elastic")
        if tag.get("name")
    }


def _parse_atar(value: str | None) -> tuple[int | None, int | None]:
    """
    Parse the 'atar' meta tag into (atar_lowest_selection_rank, atar_guaranteed).

    Format: '2026 Guaranteed ATAR 70.00, ATAR 70.15*'
    ATAR values are always <= 99.95; anything larger (e.g. a year) is not an ATAR.
    """
    if not value:
        return None, None
    guaranteed = None
    m = re.search(r"Guaranteed ATAR\s+(\d+(?:\.\d+)?)", value, re.IGNORECASE)
    if m:
        guaranteed = int(float(m.group(1)))
    m = re.search(r",\s*ATAR\s+(\d+(?:\.\d+)?)", value, re.IGNORECASE)
    if m:
        return int(float(m.group(1))), guaranteed
    m = re.search(r"\bATAR\s+(\d+(?:\.\d+)?)", value, re.IGNORECASE)
    if m:
        return int(float(m.group(1))), guaranteed
    return None, guaranteed


def _parse_duration(value: str | None) -> float | None:
    """Parse 'Full-time 3 years, Part-time 6 years' -> 3.0 (full-time years)."""
    if not value:
        return None
    m = re.search(r"full-time\s+(\d+(?:\.\d+)?)\s+year", value, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s+year", value, re.IGNORECASE)
    return float(m.group(1)) if m else None


def _parse_csp(value: str | None) -> bool | None:
    """Return True if fees_domestic indicates CSP places are available."""
    if value is None:
        return None
    return "commonwealth supported" in value.lower()
```

- [ ] **Step 2: Verify no import errors**

```bash
cd scraper && uv run python -c "from rmit import RmitScraper; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add scraper/rmit.py
git commit -m "feat: refactor RmitScraper to discover_urls / scrape_url interface"
```

---

## Task 7: Update run.py with CLI flags

**Files:**
- Modify: `scraper/run.py`

- [ ] **Step 1: Replace `scraper/run.py` entirely**

```python
"""Entry point for the course scraper.

Usage:
  uv run python run.py                        # resume all scrapers
  uv run python run.py --university monash    # resume monash only
  uv run python run.py --force                # reset all and re-scrape
  uv run python run.py --force --university monash  # reset monash only
"""
import argparse
import asyncio
import sys

from dotenv import load_dotenv

from base_scraper import BaseScraper
from db import get_pool
from monash import MonashScraper
from rmit import RmitScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    "rmit": RmitScraper,
    "monash": MonashScraper,
}


async def main(universities: list[str], force: bool) -> None:
    load_dotenv()
    pool = await get_pool()

    targets = {k: v for k, v in SCRAPERS.items() if k in universities}
    if not targets:
        print(f"No scrapers found for: {universities}. Available: {list(SCRAPERS)}")
        await pool.close()
        return

    for slug, scraper_class in targets.items():
        print(f"Running scraper: {slug}{' (force reset)' if force else ''}")
        scraper = scraper_class(pool, slug)
        try:
            count = await scraper.run(force=force)
            print(f"  {slug}: {count} courses upserted")
        except PermissionError as e:
            print(f"  {slug}: skipped — {e}")
        except Exception as e:
            print(f"  {slug}: failed — {e}")

    await pool.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run university course scrapers")
    parser.add_argument(
        "--university",
        action="append",
        dest="universities",
        metavar="SLUG",
        help="Scraper slug to run (repeatable). Defaults to all.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset queue and re-run discovery for the target universities.",
    )
    args = parser.parse_args()

    universities = args.universities or list(SCRAPERS)
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    asyncio.run(main(universities, args.force), loop_factory=loop_factory)
```

- [ ] **Step 2: Verify the CLI help works**

```bash
cd scraper && uv run python run.py --help
```

Expected output includes `--university SLUG` and `--force`.

- [ ] **Step 3: Commit**

```bash
git add scraper/run.py
git commit -m "feat: add --force and --university flags to run.py"
```

---

## Task 8: Smoke test the full run

- [ ] **Step 1: Run all unit tests to confirm nothing is broken**

```bash
cd scraper && uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run RMIT scraper with --force to verify queue is populated**

From `scraper/` directory (DATABASE_URL env var must be set to Supabase):
```bash
uv run python run.py --university rmit --force
```

Expected: lines like:
```
Running scraper: rmit (force reset)
  rmit: NNN URLs discovered (run #N)
  rmit: NNN pending URLs
  rmit: NNN courses upserted
```

- [ ] **Step 3: Run RMIT again (no --force) to verify resume skips completed URLs**

```bash
uv run python run.py --university rmit
```

Expected:
```
Running scraper: rmit
  rmit: 0 pending URLs
  rmit: 0 courses upserted
```

- [ ] **Step 4: Verify queue state in DB**

```bash
uv run python -c "
import asyncio
async def main():
    from db import get_pool
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                SELECT sr.run_number, sr.status, sr.forced,
                       COUNT(sq.id) FILTER (WHERE sq.status = 'complete') AS complete,
                       COUNT(sq.id) FILTER (WHERE sq.status = 'pending')  AS pending,
                       COUNT(sq.id) FILTER (WHERE sq.status = 'failed')   AS failed
                FROM scrape_runs sr
                LEFT JOIN scrape_queue sq ON sq.discovered_run_id = sr.id
                JOIN universities u ON sr.university_id = u.id
                WHERE u.slug = 'rmit'
                GROUP BY sr.run_number, sr.status, sr.forced
                ORDER BY sr.run_number
            ''')
            for row in await cur.fetchall():
                print(row)
    await pool.close()
import sys, selectors
loop_factory = asyncio.SelectorEventLoop if sys.platform == 'win32' else None
asyncio.run(main(), loop_factory=loop_factory)
"
```

Expected: one row per run showing complete=NNN, pending=0, failed=0.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: scraper queue — resilient resumable scraping with run tracking"
```

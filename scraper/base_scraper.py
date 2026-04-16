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

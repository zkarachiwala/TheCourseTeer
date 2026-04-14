import urllib.robotparser
from abc import ABC, abstractmethod

from psycopg_pool import AsyncConnectionPool

from db import get_university, update_university_status
from http_client import make_client
from models import CourseData
from robots import fetch_and_store_robots, is_allowed


class BaseScraper(ABC):
    """
    Base class for all university course scrapers.

    Subclasses implement scrape(rp) and are invoked via run(), which handles
    robots.txt fetching, status updates, and error logging.

    Subclasses must call self.check_robots(rp, url) before fetching each
    course URL to enforce per-path robots.txt compliance.
    """

    def __init__(self, pool: AsyncConnectionPool, university_slug: str) -> None:
        self.pool = pool
        self.slug = university_slug
        self._university: dict | None = None

    async def run(self) -> list[CourseData]:
        """
        Public entry point. Fetches and stores robots.txt, then delegates to
        scrape(rp). Updates university scraper_status on completion or failure.
        """
        self._university = await get_university(self.pool, self.slug)
        university_id = self._university["id"]

        async with make_client() as client:
            rp = await fetch_and_store_robots(
                self.pool, university_id, self._university["homepage_url"], client
            )

        try:
            courses = await self.scrape(rp)
            await update_university_status(self.pool, university_id, "last_ok")
            return courses
        except PermissionError:
            await update_university_status(self.pool, university_id, "robots_blocked")
            raise
        except Exception:
            await update_university_status(self.pool, university_id, "failing")
            raise

    @property
    def university_id(self) -> str:
        """UUID of the current university. Available after run() starts."""
        if self._university is None:
            raise RuntimeError("university_id accessed before run()")
        return str(self._university["id"])

    def check_robots(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> None:
        """Raise PermissionError if url is disallowed by robots rules."""
        if not is_allowed(rp, url):
            raise PermissionError(f"robots.txt blocks {url}")

    @abstractmethod
    async def scrape(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[CourseData]:
        """
        Extract course records for this university.

        Called by run() after robots.txt is fetched. Must call
        self.check_robots(rp, url) before fetching each course URL.
        Return a list of CourseData instances.
        """
        ...

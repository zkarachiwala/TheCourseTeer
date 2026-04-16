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
        except PermissionError:
            raise
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

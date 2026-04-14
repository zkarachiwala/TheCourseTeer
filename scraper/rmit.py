"""RMIT University course scraper (static / httpx)."""
import asyncio
import re
import urllib.robotparser
from collections.abc import Callable

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from db import get_campus_id
from http_client import make_client
from models import CourseData

SITEMAP_URL = "https://www.rmit.edu.au/sitemap.xml"
_UG_PREFIX = "/study-with-us/levels-of-study/undergraduate-study/"
# Root course URLs split to exactly 8 segments: ['https:', '', 'www.rmit.edu.au',
# 'study-with-us', 'levels-of-study', 'undergraduate-study', '<type>', '<slug>'].
# Sub-pages (apply-now, further-study, etc.) produce 9+ segments and are excluded.
_COURSE_DEPTH = 8
_CONCURRENCY = 5


class RmitScraper(BaseScraper):
    """Scraper for RMIT University. Discovers courses from sitemap.xml."""

    async def scrape(self, rp: urllib.robotparser.RobotFileParser) -> list[CourseData]:
        sem = asyncio.Semaphore(_CONCURRENCY)
        async with make_client() as client:
            urls = await _discover_urls(client)
            campus_id = await get_campus_id(self.pool, self.university_id, "rmit-city")
            tasks = [
                _scrape_one(client, rp, url, self.university_id, campus_id, sem, self.check_robots)
                for url in urls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        courses = []
        for r in results:
            if isinstance(r, PermissionError):
                raise r   # propagate so BaseScraper marks status as robots_blocked
            elif isinstance(r, CourseData):
                courses.append(r)
            elif isinstance(r, Exception):
                print(f"  rmit: page skipped — {r}")
        return courses


async def _discover_urls(client) -> list[str]:
    """Fetch sitemap.xml and return root-level UG course URLs."""
    resp = await client.get(SITEMAP_URL)
    resp.raise_for_status()
    return [
        m.group(1)
        for m in re.finditer(r"<loc>(https://[^<]+)</loc>", resp.text)
        if _UG_PREFIX in m.group(1) and len(m.group(1).split("/")) == _COURSE_DEPTH
    ]


async def _scrape_one(
    client,
    rp: urllib.robotparser.RobotFileParser,
    url: str,
    university_id: str,
    campus_id: str | None,
    sem: asyncio.Semaphore,
    check_robots: Callable,
) -> CourseData | None:
    """Fetch a single course page and return a CourseData, or None if unusable."""
    check_robots(rp, url)
    async with sem:
        resp = await client.get(url)
    if resp.status_code != 200:
        print(f"  rmit: {resp.status_code} {url}")
        return None

    meta = _parse_meta(resp.text)
    name = meta.get("product_name")
    if not name:
        return None

    mode = meta.get("learning_mode_domestic", "")
    effective_campus_id = None if "online" in mode.lower() else campus_id

    return CourseData(
        university_id=university_id,
        name=name,
        source_url=url,
        faculty=meta.get("college") or None,
        campus_id=effective_campus_id,
        degree_type="UG",
        duration_years=_parse_duration(meta.get("duration_domestic")),
        csp_available=_parse_csp(meta.get("fees_domestic")),
        price_annual_csp_aud=None,   # RMIT does not publish CSP amounts
        price_annual_dfee_aud=None,  # RMIT does not publish domestic full-fee amounts
        atar_lowest_selection_rank=_parse_atar(meta.get("atar")),
        atar_guaranteed=None,   # RMIT does not publish a separate guaranteed entry ATAR
    )


def _parse_meta(html: str) -> dict[str, str]:
    """Extract all <meta class="elastic"> tags into a name->content dict."""
    soup = BeautifulSoup(html, "lxml")
    return {
        tag["name"]: tag.get("content", "")
        for tag in soup.find_all("meta", class_="elastic")
        if tag.get("name")
    }


def _parse_atar(value: str | None) -> int | None:
    """Parse 'ATAR 75.10*' -> 75."""
    if not value:
        return None
    m = re.search(r"\d+(?:\.\d+)?", value)
    return int(float(m.group())) if m else None


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

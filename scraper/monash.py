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

    async def scrape(self, rp: urllib.robotparser.RobotFileParser) -> list[CourseData]:
        campus_map = await get_campus_map(self.pool, self.university_id)

        # Playwright must run in a separate thread with its own event loop on Windows.
        loop = asyncio.get_running_loop()
        check_robots = self.check_robots
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            url_html_pairs: list[tuple[str, str]] = await loop.run_in_executor(
                executor,
                lambda: asyncio.run(_playwright_fetch_all(rp, check_robots)),
            )

        courses = []
        for url, html in url_html_pairs:
            c = _parse_course(html, url, self.university_id, campus_map)
            if c:
                courses.append(c)
        return courses


async def _playwright_fetch_all(
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
) -> list[tuple[str, str]]:
    """
    Run inside asyncio.run() in a thread. Fetches listing page + all course pages
    via Playwright. Returns list of (url, html) pairs for successful fetches.
    """
    async with browser_context() as ctx:
        urls = await _discover_urls(ctx, rp, check_robots)
        sem = asyncio.Semaphore(_CONCURRENCY)
        tasks = [_fetch_page(ctx, url, rp, check_robots, sem) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    pairs: list[tuple[str, str]] = []
    for r in results:
        if isinstance(r, PermissionError):
            raise r  # propagate so BaseScraper marks robots_blocked
        elif isinstance(r, tuple):
            pairs.append(r)
        elif isinstance(r, Exception):
            print(f"  monash: page skipped — {r}")
    return pairs


async def _discover_urls(
    ctx: BrowserContext,
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
) -> list[str]:
    """Load the course listing page and return degree-course URLs."""
    check_robots(rp, LISTING_URL)
    page = await ctx.new_page()
    try:
        await page.goto(LISTING_URL, wait_until="networkidle", timeout=30000)
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


async def _fetch_page(
    ctx: BrowserContext,
    url: str,
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
    sem: asyncio.Semaphore,
) -> tuple[str, str]:
    """Fetch a single course page and return (url, html)."""
    check_robots(rp, url)
    async with sem:
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
        finally:
            await page.close()
    return url, html


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
        # Fallback: infer from URL code prefix (b = bachelor/UG, others = PG)
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
        faculty=None,  # not published on Monash course pages
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
    # "On-campus at Caulfield: Full time & part time" -> "Caulfield"
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

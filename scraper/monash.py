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
from models import CampusLink, CourseData

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
    duration = _parse_duration(table.get("Duration", ""))
    csp_fee, dfee = _parse_fees(html)
    campuses = _build_campus_links(soup, table.get("Location", ""), campus_map)

    return CourseData(
        university_id=university_id,
        name=name,
        source_url=url,
        faculty=None,
        campuses=campuses,
        degree_type=degree_type,
        duration_years=duration,
        price_annual_csp_aud=csp_fee,
        price_annual_dfee_aud=dfee,
        csp_available=csp_fee is not None,
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


def _build_campus_links(
    soup: BeautifulSoup, location: str, campus_map: dict[str, str]
) -> list[CampusLink]:
    """Build CampusLink list with per-campus ATAR extracted from campus sections."""
    links: list[CampusLink] = []

    for raw in re.findall(r"on.campus at ([^,:]+)", location, re.IGNORECASE):
        raw = raw.strip()
        campus_id = next(
            (cid for name, cid in campus_map.items() if name.lower() == raw.lower()),
            None,
        )
        if campus_id is None:
            print(f"  monash: unrecognised campus '{raw}' in location '{location}'")
            continue
        atar_rank, atar_guaranteed, notes = _parse_atar_in_section(soup, raw)
        links.append(CampusLink(
            campus_id=campus_id,
            atar_guaranteed=atar_guaranteed,
            atar_lowest_selection_rank=atar_rank,
            extraction_notes=notes,
        ))

    if "online" in location.lower():
        online_id = campus_map.get("Online")
        if online_id:
            links.append(CampusLink(campus_id=online_id))

    return links


def _parse_atar_in_section(
    soup: BeautifulSoup, campus_name: str
) -> tuple[int | None, int | None, str | None]:
    """Extract ATAR from the campus-specific page section; fall back to global."""
    slug = campus_name.lower().replace(" ", "-")
    section = soup.find(id=slug) or soup.find(id=campus_name.lower())
    notes = None if section else "ATAR from global page (no campus section found)"
    atar_rank, atar_guaranteed = _parse_atar(section if section else soup)
    return atar_rank, atar_guaranteed, notes


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


def _parse_atar(tag) -> tuple[int | None, int | None]:
    """
    Return (atar_lowest_selection_rank, atar_guaranteed) from course-page__subject-req-item
    elements within tag. Values are integers (fractional parts truncated).
    """
    atar_rank: int | None = None
    atar_guaranteed: int | None = None
    for div in tag.find_all("div", class_="course-page__subject-req-item"):
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

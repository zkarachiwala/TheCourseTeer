"""University of Melbourne course scraper (Playwright — Nuxt.js SPA).

Discovery: XHR interception on the UG listing page — captures JSON responses
from Nuxt's backend API to collect course URLs without relying on DOM link
structure. Falls back to regex over rendered HTML if no JSON intercept matches.

Per-course: Playwright renders each page (waitUntil=networkidle), then parses
the resulting HTML. CSP fee lookup is deferred — price_annual_csp_aud is left
null until the fees tab scraping pass is implemented.
"""
import asyncio
import concurrent.futures
import re
import urllib.robotparser
from collections.abc import Callable

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from base_scraper import BaseScraper
from browser import browser_context
from db import get_campus_map, log_atar_issue
from models import CampusLink, CourseData

LISTING_URL = "https://study.unimelb.edu.au/find/courses/undergraduate/"
_BASE_URL = "https://study.unimelb.edu.au"
_COURSE_PATH_RE = re.compile(r"^/find/courses/undergraduate/[^/]+/$")
_CONCURRENCY = 3

# Checked in order; first match wins. Keywords matched against lowercased course name.
_FACULTY_MAP: list[tuple[str, list[str]]] = [
    ("Faculty of Fine Arts and Music", [
        "music", "fine art", "visual art", "theatre", "drama", "dance",
        "film", "animation", "creative arts",
    ]),
    ("Faculty of Law", ["laws", "legal studies"]),
    ("Faculty of Medicine, Dentistry and Health Sciences", [
        "medicine", "biomedicine", "dentistry", "dental", "health sciences",
        "nursing", "physiotherapy", "pharmacy", "optometry", "oral health",
        "speech pathology", "occupational therapy", "midwifery", "paramedicine",
    ]),
    ("Faculty of Education", ["education", "teaching"]),
    ("Faculty of Engineering and Information Technology", [
        "engineering", "computing", "information technology",
        "information systems", "mechatron", "data science",
    ]),
    ("Faculty of Science", [
        "science", "biology", "chemistry", "physics", "mathematics",
        "statistics", "ecology", "genetics", "neuroscience", "geology",
    ]),
    ("Faculty of Business and Economics", [
        "commerce", "economics", "business", "accounting", "finance",
        "management", "marketing", "actuarial",
    ]),
    ("Faculty of Architecture, Building and Planning", [
        "architecture", "environments", "construction", "urban",
        "landscape", "property", "planning",
    ]),
    ("Faculty of Arts", [
        "arts", "humanities", "social science", "history", "philosophy",
        "linguistics", "media", "communications", "politics", "criminology",
        "psychology", "sociology", "geography", "anthropology", "cultural",
    ]),
    ("Faculty of Veterinary and Agricultural Sciences", [
        "veterinary", "agriculture", "food", "animal science", "forest",
    ]),
]

_CAMPUS_NAMES = {
    "parkville": "Parkville",
    "southbank": "Southbank",
    "online": "Online",
}


def _infer_faculty(course_name: str) -> str | None:
    lower = course_name.lower()
    for faculty, keywords in _FACULTY_MAP:
        if any(kw in lower for kw in keywords):
            return faculty
    return None


class UniMelbScraper(BaseScraper):
    """Scraper for University of Melbourne. Uses Playwright for Nuxt.js SPA."""

    _CONCURRENCY = _CONCURRENCY

    async def discover_urls(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[str]:
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
        raise NotImplementedError("UniMelbScraper fetches via _process_batch")

    async def _process_batch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        urls: list[str],
    ) -> list[tuple[str, CourseData | Exception | None]]:
        if not urls:
            return []
        campus_map = await get_campus_map(self.pool, self.university_id)
        loop = asyncio.get_running_loop()
        check_robots = self.check_robots
        university_id = self.university_id
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            raw = await loop.run_in_executor(
                ex,
                lambda: asyncio.run(
                    _playwright_fetch_batch(rp, check_robots, urls, university_id, campus_map)
                ),
            )
        for url, result, issues in raw:
            name = result.name if isinstance(result, CourseData) else url
            for issue_type, description in issues:
                await log_atar_issue(
                    self.pool, self.university_id, self._run_id,
                    name, url, issue_type, description,
                )
        return [(url, result) for url, result, _ in raw]


async def _playwright_discover(
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
) -> list[str]:
    """Open listing page, intercept JSON responses, extract course URLs."""
    check_robots(rp, LISTING_URL)
    course_urls: set[str] = set()

    async with browser_context() as ctx:
        page = await ctx.new_page()
        json_responses: list = []

        async def _on_response(response):
            if "json" in response.headers.get("content-type", ""):
                try:
                    json_responses.append(await response.json())
                except Exception:
                    pass

        page.on("response", _on_response)
        try:
            await page.goto(LISTING_URL, wait_until="networkidle", timeout=60000)
            html = await page.content()
        finally:
            await page.close()

    # XHR intercept: walk any JSON structure looking for course URL patterns
    for data in json_responses:
        _collect_urls_from_json(data, course_urls)

    # DOM fallback: find hrefs matching the UG course path pattern
    if not course_urls:
        print("  unimelb: no course URLs from XHR intercept — falling back to DOM parse")
        for m in re.finditer(r'href="(/find/courses/undergraduate/[^/"]+/)"', html):
            course_urls.add(_BASE_URL + m.group(1))

    return list(course_urls)


def _collect_urls_from_json(data, found: set[str]) -> None:
    """Recursively walk a JSON structure and collect UG course URLs."""
    if isinstance(data, dict):
        for v in data.values():
            # Check for URL-like string values matching the course path pattern
            if isinstance(v, str) and _COURSE_PATH_RE.match(v):
                found.add(_BASE_URL + v)
            elif isinstance(v, str) and _BASE_URL in v:
                path = v.replace(_BASE_URL, "")
                if _COURSE_PATH_RE.match(path):
                    found.add(v if v.startswith("http") else _BASE_URL + path)
            else:
                _collect_urls_from_json(v, found)
    elif isinstance(data, list):
        for item in data:
            _collect_urls_from_json(item, found)


async def _playwright_fetch_batch(
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
    urls: list[str],
    university_id: str,
    campus_map: dict[str, str],
) -> list[tuple[str, CourseData | Exception | None, list[tuple[str, str]]]]:
    async with browser_context() as ctx:
        sem = asyncio.Semaphore(_CONCURRENCY)
        tasks = [
            _fetch_one(ctx, rp, check_robots, url, university_id, campus_map, sem)
            for url in urls
        ]
        return list(await asyncio.gather(*tasks))


async def _fetch_one(
    ctx: BrowserContext,
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
    url: str,
    university_id: str,
    campus_map: dict[str, str],
    sem: asyncio.Semaphore,
) -> tuple[str, CourseData | Exception | None, list[tuple[str, str]]]:
    check_robots(rp, url)
    async with sem:
        await asyncio.sleep(2)
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("h1", timeout=30000)
            html = await page.content()
        except Exception as e:
            return url, e, []
        finally:
            await page.close()
    result, issues = _parse_course(html, url, university_id, campus_map)
    return url, result, issues


def _parse_course(
    html: str,
    url: str,
    university_id: str,
    campus_map: dict[str, str],
) -> tuple[CourseData | None, list[tuple[str, str]]]:
    soup = BeautifulSoup(html, "lxml")
    issues: list[tuple[str, str]] = []

    name = _parse_name(soup)
    if not name:
        return None, issues

    duration = _parse_duration(soup)
    campuses = _build_campus_links(soup, campus_map, name, url, issues)

    return CourseData(
        university_id=university_id,
        name=name,
        source_url=url,
        faculty=_infer_faculty(name),
        campuses=campuses,
        degree_type="UG",
        duration_years=duration,
        csp_available=True,
        price_annual_csp_aud=None,   # deferred: fees tab pass not yet implemented
        price_annual_dfee_aud=None,  # Melbourne UG has no domestic full-fee places
    ), issues


def _parse_name(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if not h1:
        return None
    name = h1.get_text(strip=True)
    # Skip generic error/loading pages
    return name if len(name) > 5 else None


def _parse_duration(soup: BeautifulSoup) -> float | None:
    text = soup.get_text(" ")
    # Match patterns like "3 years full-time" or "4-year" anywhere in page text
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-\s]?year", text, re.IGNORECASE)
    return float(m.group(1)) if m else None


def _build_campus_links(
    soup: BeautifulSoup,
    campus_map: dict[str, str],
    course_name: str,
    url: str,
    issues: list[tuple[str, str]],
) -> list[CampusLink]:
    """Detect campus from page content and build CampusLink list.

    Flags both-campus courses in issues for manual review.
    """
    page_text = soup.get_text(" ").lower()
    links: list[CampusLink] = []

    has_parkville = "parkville" in page_text
    has_southbank = "southbank" in page_text
    has_online = re.search(r"\bonline\b", page_text) is not None

    if has_parkville:
        campus_id = campus_map.get("Parkville")
        if campus_id:
            atar_rank, atar_guaranteed = _parse_atar_near_campus(soup, "parkville")
            links.append(CampusLink(
                campus_id=campus_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
            ))

    if has_southbank:
        campus_id = campus_map.get("Southbank")
        if campus_id:
            atar_rank, atar_guaranteed = _parse_atar_near_campus(soup, "southbank")
            links.append(CampusLink(
                campus_id=campus_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
            ))

    if has_parkville and has_southbank:
        issues.append((
            "multiple_campuses",
            f"Course '{course_name}' appears at both Parkville and Southbank — verify campus split",
        ))

    if has_online:
        online_id = campus_map.get("Online")
        if online_id:
            links.append(CampusLink(campus_id=online_id))

    # If no campus detected, default to Parkville (Melbourne's primary campus)
    if not links:
        parkville_id = campus_map.get("Parkville")
        if parkville_id:
            atar_rank, atar_guaranteed = _parse_atar_near_campus(soup, None)
            links.append(CampusLink(
                campus_id=parkville_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
                extraction_notes="Campus not detected on page — defaulted to Parkville",
            ))

    return links


def _parse_atar_near_campus(
    soup: BeautifulSoup, campus_slug: str | None
) -> tuple[int | None, int | None]:
    """Extract ATAR values near a campus section, or globally if campus_slug is None."""
    # Try to find a section/heading containing the campus name first
    section = None
    if campus_slug:
        for tag in soup.find_all(["h2", "h3", "h4", "section", "div"]):
            if campus_slug in tag.get_text().lower():
                section = tag.find_parent(["section", "div"]) or tag
                break

    search_root = section if section else soup
    return _extract_atar_values(search_root)


def _extract_atar_values(
    root: BeautifulSoup,
) -> tuple[int | None, int | None]:
    """Scan root for ATAR/selection rank numbers. Returns (lowest_rank, guaranteed)."""
    text = root.get_text(" ")
    atar_rank: int | None = None
    atar_guaranteed: int | None = None

    # Match patterns like "Lowest selection rank 75" or "Selection rank: 75.00"
    m = re.search(
        r"(?:lowest\s+)?selection\s+rank[:\s]+(\d{2,3}(?:\.\d+)?)",
        text, re.IGNORECASE,
    )
    if m:
        atar_rank = int(float(m.group(1)))

    # Match "Guaranteed ATAR 90" or "Guaranteed entry: 90"
    m = re.search(
        r"guaranteed\s+(?:atar|entry)[:\s]+(\d{2,3}(?:\.\d+)?)",
        text, re.IGNORECASE,
    )
    if m:
        atar_guaranteed = int(float(m.group(1)))

    return atar_rank, atar_guaranteed

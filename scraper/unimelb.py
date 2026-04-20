"""University of Melbourne course scraper (Playwright + Funnelback JSON API).

Discovery: Load the UoM course search page via Playwright (for Cloudflare clearance),
then use page.evaluate() to call the Funnelback JSON API from within the browser.
The API returns structured metadata including course URLs, names, and ATAR data.

Per-course: Playwright renders each course page to extract duration and campus.
All other data (name, ATAR, CSP flag) comes from the Funnelback metadata.

CSP fee amounts are deferred — price_annual_csp_aud is left null.
"""
import asyncio
import concurrent.futures
import re
import urllib.robotparser
from collections.abc import Callable
from dataclasses import dataclass

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from base_scraper import BaseScraper
from browser import browser_context
from db import get_campus_map, log_atar_issue
from models import CampusLink, CourseData

# Load this page first to get Cloudflare clearance for the funnelback domain
_CF_CLEARANCE_URL = "https://study.unimelb.edu.au/find?collection=uom%7Esp-courses&profile=_default&query=%21showall"
_FUNNELBACK_URL = "https://uom-search.funnelback.squiz.cloud/s/search.json"
_BASE_URL = "https://study.unimelb.edu.au"
_CONCURRENCY = 3

_FUNNELBACK_JS = """async () => {
    const params = new URLSearchParams({
        'collection': 'uom~sp-courses',
        'profile': '_default',
        'query': '!showall',
        'num_ranks': '200',
        'start_rank': '1',
        'sort': 'metacourseDisplayTitle',
        'f.Study level|courseStudyLevel': 'undergraduate',
    });
    const url = 'https://uom-search.funnelback.squiz.cloud/s/search.json?' + params.toString();
    const resp = await fetch(url, {headers: {'Referer': 'https://study.unimelb.edu.au/'}});
    return resp.json();
}"""

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
        "mathematical sciences",
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
        "languages",
    ]),
    ("Faculty of Veterinary and Agricultural Sciences", [
        "veterinary", "agriculture", "food", "animal science", "forest",
    ]),
]


@dataclass
class _ListingEntry:
    name: str
    atar_guaranteed: int | None
    atar_rank: int | None
    csp_available: bool


def _infer_faculty(course_name: str) -> str | None:
    lower = course_name.lower()
    for faculty, keywords in _FACULTY_MAP:
        if any(kw in lower for kw in keywords):
            return faculty
    return None


def _parse_atar_from_entry_requirements(html: str) -> tuple[int | None, int | None]:
    """Parse guaranteed ATAR and lowest selection rank from Funnelback metadata HTML.

    Format: '<strong>72.00</strong> - Guaranteed ATAR 2026 <br>
             <strong>72.75</strong> - Lowest selection rank 2025 (guide only)'
    Returns (atar_guaranteed, atar_rank).
    """
    if not html:
        return None, None
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ").lower()
    guaranteed = None
    rank = None
    for strong in soup.find_all("strong"):
        try:
            val = int(float(strong.get_text(strip=True)))
        except ValueError:
            continue
        # Determine what this number refers to from following text context
        following = strong.find_next_sibling(string=True) or ""
        if not isinstance(following, str):
            following = ""
        following = following.lower()
        parent_text = (strong.parent.get_text(" ") if strong.parent else "").lower()
        if "guaranteed" in following or "guaranteed" in parent_text:
            guaranteed = val
        elif "lowest selection rank" in following or "lowest selection rank" in parent_text:
            rank = val
    # Fallback: if we couldn't match by context, use position
    if guaranteed is None and rank is None:
        nums = []
        for strong in soup.find_all("strong"):
            try:
                nums.append(int(float(strong.get_text(strip=True))))
            except ValueError:
                pass
        if "guaranteed" in text and nums:
            guaranteed = nums[0]
        if "lowest selection rank" in text and len(nums) > 1:
            rank = nums[1]
    return guaranteed, rank


class UniMelbScraper(BaseScraper):
    """Scraper for University of Melbourne."""

    _CONCURRENCY = _CONCURRENCY

    def __init__(self, pool, university_slug: str) -> None:
        super().__init__(pool, university_slug)
        self._listing: dict[str, _ListingEntry] = {}

    async def discover_urls(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[str]:
        loop = asyncio.get_running_loop()
        check_robots = self.check_robots
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            listing = await loop.run_in_executor(
                ex,
                lambda: asyncio.run(_playwright_discover(rp, check_robots)),
            )
        self._listing = listing
        return list(listing.keys())

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
        listing = self._listing
        loop = asyncio.get_running_loop()
        check_robots = self.check_robots
        university_id = self.university_id
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            raw = await loop.run_in_executor(
                ex,
                lambda: asyncio.run(
                    _playwright_fetch_batch(
                        rp, check_robots, urls, university_id, campus_map, listing
                    )
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
) -> dict[str, _ListingEntry]:
    """Load search page for CF clearance, then call Funnelback API via page.evaluate()."""
    check_robots(rp, _CF_CLEARANCE_URL)
    async with browser_context() as ctx:
        page = await ctx.new_page()
        try:
            await page.goto(_CF_CLEARANCE_URL, wait_until="networkidle", timeout=60000)
            data = await page.evaluate(_FUNNELBACK_JS)
        finally:
            await page.close()

    results = (
        data.get("response", {})
        .get("resultPacket", {})
        .get("results", [])
    )
    listing: dict[str, _ListingEntry] = {}
    for result in results:
        url = result.get("liveUrl") or result.get("indexUrl") or ""
        if "/find/courses/undergraduate/" not in url:
            continue
        meta = result.get("listMetadata", {})
        name = (meta.get("courseDisplayTitle") or [""])[0]
        if not name:
            continue
        entry_req_html = (meta.get("courseEntryRequirements") or [""])[0]
        atar_guaranteed, atar_rank = _parse_atar_from_entry_requirements(entry_req_html)
        fees = (meta.get("courseFeesDomestic") or [""])[0].lower()
        csp_available = "commonwealth supported" in fees
        listing[url] = _ListingEntry(
            name=name,
            atar_guaranteed=atar_guaranteed,
            atar_rank=atar_rank,
            csp_available=csp_available,
        )

    print(f"  unimelb: {len(listing)} UG courses from Funnelback API")
    return listing


async def _playwright_fetch_batch(
    rp: urllib.robotparser.RobotFileParser,
    check_robots: Callable,
    urls: list[str],
    university_id: str,
    campus_map: dict[str, str],
    listing: dict[str, _ListingEntry],
) -> list[tuple[str, CourseData | Exception | None, list[tuple[str, str]]]]:
    async with browser_context() as ctx:
        sem = asyncio.Semaphore(_CONCURRENCY)
        tasks = [
            _fetch_one(ctx, rp, check_robots, url, university_id, campus_map, listing, sem)
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
    listing: dict[str, _ListingEntry],
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
    entry = listing.get(url)
    result, issues = _parse_course(html, url, university_id, campus_map, entry)
    return url, result, issues


def _parse_course(
    html: str,
    url: str,
    university_id: str,
    campus_map: dict[str, str],
    entry: _ListingEntry | None,
) -> tuple[CourseData | None, list[tuple[str, str]]]:
    soup = BeautifulSoup(html, "lxml")
    issues: list[tuple[str, str]] = []

    # Prefer h1 for full specialisation name (e.g. "Bachelor of Fine Arts (Acting)")
    name = _parse_name(soup) or (entry.name if entry else None)
    if not name:
        return None, issues

    atar_guaranteed = entry.atar_guaranteed if entry else None
    atar_rank = entry.atar_rank if entry else None
    csp_available = entry.csp_available if entry else True
    duration = _parse_duration(soup)
    campuses = _build_campus_links(
        soup, campus_map, name, url, issues, atar_guaranteed, atar_rank,
    )

    return CourseData(
        university_id=university_id,
        name=name,
        source_url=url,
        faculty=_infer_faculty(name),
        campuses=campuses,
        degree_type="UG",
        duration_years=duration,
        csp_available=csp_available,
        price_annual_csp_aud=None,   # deferred: fees tab pass not yet implemented
        price_annual_dfee_aud=None,  # Melbourne UG has no domestic full-fee places
    ), issues


def _parse_name(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if not h1:
        return None
    name = h1.get_text(strip=True)
    return name if len(name) > 5 else None


def _parse_duration(soup: BeautifulSoup) -> float | None:
    text = soup.get_text(" ")
    m = re.search(r"(\d+(?:\.\d+)?)\s+years?\s+(?:full.?time|standard)", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)[- ]year", text, re.IGNORECASE)
    return float(m.group(1)) if m else None


def _build_campus_links(
    soup: BeautifulSoup,
    campus_map: dict[str, str],
    course_name: str,
    url: str,
    issues: list[tuple[str, str]],
    atar_guaranteed: int | None,
    atar_rank: int | None,
) -> list[CampusLink]:
    page_text = soup.get_text(" ").lower()
    has_parkville = "parkville" in page_text
    has_southbank = "southbank" in page_text
    has_online = bool(re.search(r"\bonline\b", page_text))
    links: list[CampusLink] = []

    if has_parkville and has_southbank:
        parkville_id = campus_map.get("Parkville")
        southbank_id = campus_map.get("Southbank")
        if parkville_id:
            links.append(CampusLink(
                campus_id=parkville_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
            ))
        if southbank_id:
            links.append(CampusLink(
                campus_id=southbank_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
            ))
        issues.append((
            "multiple_campuses",
            f"'{course_name}' appears at both Parkville and Southbank — verify campus split",
        ))
    elif has_southbank:
        campus_id = campus_map.get("Southbank")
        if campus_id:
            links.append(CampusLink(
                campus_id=campus_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
            ))
    else:
        campus_id = campus_map.get("Parkville")
        if campus_id:
            notes = None if has_parkville else "Campus not detected on page — defaulted to Parkville"
            links.append(CampusLink(
                campus_id=campus_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
                extraction_notes=notes,
            ))

    if has_online:
        online_id = campus_map.get("Online")
        if online_id:
            links.append(CampusLink(campus_id=online_id))

    return links

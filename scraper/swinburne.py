"""Swinburne University of Technology course scraper (static / httpx)."""
import asyncio
import re
import urllib.robotparser

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from db import get_campus_map, log_atar_issue
from http_client import make_client
from models import CampusLink, CourseData

SITEMAP_URL = "https://www.swinburne.edu.au/course/sitemap.xml"
_UG_PATH = "/course/undergraduate/"
_CONCURRENCY = 5

# Swinburne's campus div text matches DB names exactly ("Hawthorn", "Wantirna", "Online").
# Extend this map if a mismatch is ever discovered.
_LOCATION_MAP: dict[str, str] = {}

# Checked in order; first match wins.
_FACULTY_MAP: list[tuple[str, list[str]]] = [
    ("Faculty of Science, Engineering and Technology", [
        "engineering", "science", "computing", "computer", "technology",
        "information technology", "data science", "cybersecurity",
        "telecommunications", "robotics", "mechatronics", "aviation",
        "manufacturing", "construction", "architecture",
    ]),
    ("Faculty of Business and Law", [
        "business", "commerce", "accounting", "finance", "marketing",
        "management", "law", "legal",
    ]),
    ("Faculty of Health, Arts and Design", [
        "health", "nursing", "psychology", "design", "film", "television",
        "games", "animation", "media", "communication", "arts",
        "humanities", "education", "social",
    ]),
]


class SwinburneScraper(BaseScraper):
    """Scraper for Swinburne University. Uses httpx for static page fetching."""

    _CONCURRENCY = _CONCURRENCY

    async def discover_urls(
        self, rp: urllib.robotparser.RobotFileParser
    ) -> list[str]:
        """Fetch course sitemap and return all undergraduate course URLs."""
        self.check_robots(rp, SITEMAP_URL)
        async with make_client() as client:
            resp = await client.get(SITEMAP_URL)
            resp.raise_for_status()
            return [
                m.group(1)
                for m in re.finditer(r"<loc>(https://[^<]+)</loc>", resp.text)
                if _UG_PATH in m.group(1)
            ]

    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        raise NotImplementedError("SwinburneScraper fetches via _process_batch")

    async def _process_batch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        urls: list[str],
    ) -> list[tuple[str, CourseData | Exception | None]]:
        if not urls:
            return []
        campus_map = await get_campus_map(self.pool, self.university_id)
        sem = asyncio.Semaphore(self._CONCURRENCY)
        async with make_client() as client:
            tasks = [
                self._safe_fetch(rp, url, client, campus_map, sem) for url in urls
            ]
            return list(await asyncio.gather(*tasks))

    async def _safe_fetch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        url: str,
        client,
        campus_map: dict[str, str],
        sem: asyncio.Semaphore,
    ) -> tuple[str, CourseData | Exception | None]:
        self.check_robots(rp, url)
        try:
            async with sem:
                resp = await client.get(url)
            if resp.status_code != 200:
                print(f"  swinburne: {resp.status_code} {url}")
                return url, None
            return url, await self._parse(url, resp.text, campus_map)
        except Exception as e:
            return url, e

    async def _parse(
        self,
        url: str,
        html: str,
        campus_map: dict[str, str],
    ) -> CourseData | None:
        soup = BeautifulSoup(html, "lxml")
        name = _parse_name(soup)
        if not name:
            return None

        atar_guaranteed, atar_rank, csp_fee = _parse_fees_block(soup)
        campuses, issues = _build_campus_links(
            soup, campus_map, atar_guaranteed, atar_rank
        )

        online_id = campus_map.get("Online")
        physical = [c for c in campuses if c.campus_id != online_id]
        if physical and all(
            c.atar_guaranteed is None and c.atar_lowest_selection_rank is None
            for c in physical
        ):
            issues.append(_classify_no_atar(url, name, soup))

        for issue_type, description in issues:
            await log_atar_issue(
                self.pool, self.university_id, self._run_id,
                name, url, issue_type, description,
            )

        return CourseData(
            university_id=self.university_id,
            name=name,
            source_url=url,
            faculty=_infer_faculty(name),
            campuses=campuses,
            degree_type="UG",
            duration_years=_parse_duration(soup),
            csp_available=len(physical) > 0,
            price_annual_csp_aud=csp_fee,
            price_annual_dfee_aud=None,
        )


def _parse_name(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if not h1:
        return None
    name = h1.get_text(strip=True)
    return name if len(name) > 5 else None


def _parse_fees_block(
    soup: BeautifulSoup,
) -> tuple[int | None, int | None, int | None]:
    """Parse all course-fees__block entries in one pass.

    Returns (atar_guaranteed, atar_lowest_selection_rank, csp_fee_annual).
    ATAR values are integers <= 100; fee values are integers > 100.
    """
    guaranteed: int | None = None
    rank: int | None = None
    csp_fee: int | None = None
    for block in soup.find_all("div", class_="course-fees__block"):
        h4 = block.find("h4", class_="course-fees__sub-title")
        total = block.find("p", class_="course-fees__total")
        if not h4 or not total:
            continue
        label = h4.get_text(strip=True).lower()
        raw = total.get_text(strip=True).replace("$", "").replace(",", "")
        try:
            val = int(float(raw))
        except ValueError:
            continue
        block_classes = block.get("class", [])
        is_domestic = "domestic" in block_classes
        is_international = "international" in block_classes
        if "guaranteed" in label and val <= 100:
            guaranteed = val
        elif "lowest" in label and val <= 100:
            rank = val
        elif "yearly fee" in label and is_domestic and not is_international and val > 100:
            csp_fee = val

    # Fallback: some courses (e.g. Associate Degrees) only show ATAR in the
    # summary tile, not in the detailed fees section.
    if guaranteed is None and rank is None:
        summary = soup.find("div", class_="course-details__atar")
        if summary:
            p = summary.find("p", class_="h3")
            if p:
                try:
                    guaranteed = int(float(p.get_text(strip=True)))
                except ValueError:
                    pass

    return guaranteed, rank, csp_fee


def _parse_duration(soup: BeautifulSoup) -> float | None:
    """Extract full-time duration years from course-details__duration."""
    div = soup.find("div", class_="course-details__duration")
    if not div:
        return None
    span = div.find("span", class_="domestic")
    text = span.get_text(strip=True) if span else div.get_text(strip=True)
    m = re.search(r"(\d+(?:\.\d+)?)\s+years?\s+full.?time", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s+years?", text, re.IGNORECASE)
    return float(m.group(1)) if m else None


def _build_campus_links(
    soup: BeautifulSoup,
    campus_map: dict[str, str],
    atar_guaranteed: int | None,
    atar_rank: int | None,
) -> tuple[list[CampusLink], list[tuple[str, str]]]:
    """Build CampusLink list from campus text in course-details__campus div."""
    campuses: list[CampusLink] = []
    issues: list[tuple[str, str]] = []

    div = soup.find("div", class_="course-details__campus")
    campus_text = div.get_text(strip=True) if div else ""
    raw_names = [n.strip() for n in campus_text.split(",") if n.strip()]

    has_online = False
    for raw in raw_names:
        if raw.lower() == "online":
            has_online = True
            continue
        db_name = _LOCATION_MAP.get(raw, raw)
        campus_id = campus_map.get(db_name)
        if campus_id is None:
            issues.append((
                "campus_not_found",
                f"Campus '{raw}' (mapped: '{db_name}') not in campus map",
            ))
            continue
        campuses.append(CampusLink(
            campus_id=campus_id,
            atar_guaranteed=atar_guaranteed,
            atar_lowest_selection_rank=atar_rank,
        ))

    if has_online:
        online_id = campus_map.get("Online")
        if online_id:
            campuses.append(CampusLink(campus_id=online_id))

    return campuses, issues


def _classify_no_atar(url: str, name: str, soup: BeautifulSoup) -> tuple[str, str]:
    """Return (issue_type, description) for a physical-campus course with no ATAR."""
    page_text = soup.get_text(" ", strip=True).lower()
    if name.lower().startswith("diploma") or "diploma" in url.lower():
        return "diploma_entry", "Diploma — typically portfolio or work-experience entry, not ATAR-based"
    if name.lower().endswith("(honours)") or "/honours" in url.lower():
        return "honours_entry", "Honours degree — undergraduate entry via completed bachelor, not ATAR-based"
    if "portfolio" in page_text:
        return "portfolio_entry", "Portfolio-based entry — no ATAR requirement listed"
    return "no_atar_unknown", "No ATAR found — reason could not be determined from page content"


def _infer_faculty(course_name: str) -> str | None:
    lower = course_name.lower()
    for faculty, keywords in _FACULTY_MAP:
        if any(kw in lower for kw in keywords):
            return faculty
    return None

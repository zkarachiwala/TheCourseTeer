"""La Trobe University course scraper (static / httpx)."""
import asyncio
import json
import re
import urllib.robotparser

from base_scraper import BaseScraper
from db import get_campus_map, log_atar_issue
from http_client import make_client
from models import CampusLink, CourseData

SITEMAP_URL = "https://www.latrobe.edu.au/sitemap.xml"
_COURSES_PATH = "/courses/"
_CONCURRENCY = 1  # respect Crawl-delay: 5

# Translate La Trobe campus codes to DB campus names
_CAMPUS_CODE_MAP: dict[str, str] = {
    "BU": "Bundoora",
    "BE": "Bendigo",
    "WO": "Albury-Wodonga",
    "CI": "Melbourne City",
    "ON": "Online",
}

# Checked in order; first match wins.
_FACULTY_MAP: list[tuple[str, list[str]]] = [
    ("School of Engineering and Mathematical Sciences", [
        "engineering", "mathematics", "maths", "statistics", "computing",
        "computer", "information technology", "data science", "cybersecurity", "software",
    ]),
    ("School of Business", [
        "business", "commerce", "accounting", "finance", "marketing",
        "management", "economics", "banking", "entrepreneurship",
    ]),
    ("School of Education", [
        "education", "teaching", "early childhood",
    ]),
    ("School of Health and Biomedical Sciences", [
        "health", "nursing", "midwifery", "paramedicine", "biomedicine", "biomedical",
        "pharmaceutical", "pharmacy", "dental", "dentistry", "podiatry", "physiotherapy",
        "orthoptics", "prosthetics", "orthotics", "optometry", "occupational therapy",
        "speech pathology", "nutrition", "dietetics", "medical laboratory",
    ]),
    ("School of Humanities and Social Sciences", [
        "arts", "humanities", "social work", "psychology", "sociology", "criminology",
        "history", "philosophy", "media", "communication", "creative arts", "music",
        "design", "law", "legal", "politics", "international", "global", "archaeology",
        "anthropology", "sport", "outdoor", "language", "linguistics",
    ]),
    ("School of Life Sciences", [
        "science", "biology", "chemistry", "physics", "environmental", "ecology",
        "genetics", "zoology", "botany", "wildlife", "agriculture", "food", "viticulture",
    ]),
]


class LaTrobeScraper(BaseScraper):
    """Scraper for La Trobe University. Uses httpx for static page fetching."""

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
                if _COURSES_PATH in m.group(1) and m.group(1) != "https://www.latrobe.edu.au/courses/a-z"
            ]

    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        raise NotImplementedError("LaTrobeScraper fetches via _process_batch")

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
                print(f"  latrobe: {resp.status_code} {url}")
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
        # 1. Course level — skip PG
        m = re.search(r'"courseLevelCode"\s*:\s*"(\w+)"', html)
        if not m or m.group(1) != "UG":
            return None

        # 2. Course name
        m = re.search(r'"advertisedTitle"\s*:\s*"([^"]+)"', html)
        if not m:
            return None
        name = m.group(1).strip()
        if len(name) < 5:
            return None

        # 3. Duration (integer or decimal string like "3" or "4.5")
        duration = _parse_duration(html)

        # 4. Campus codes list
        m = re.search(r'"campuses"\s*:\s*(\[[^\]]+\])', html)
        campus_codes = json.loads(m.group(1)) if m else []

        # 5. allAtars — keyed by year then campus code
        atar_map = _parse_all_atars(html)

        # 6. Build campus links
        campuses, issues = _build_campus_links(campus_codes, atar_map, campus_map)

        # 7. Classify no-ATAR physical campuses
        online_id = campus_map.get("Online")
        physical = [c for c in campuses if c.campus_id != online_id]
        if physical and all(
            c.atar_guaranteed is None and c.atar_lowest_selection_rank is None
            for c in physical
        ):
            issues.append(_classify_no_atar(url, name, html))

        # 8. Log issues
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
            duration_years=duration,
            csp_available=len(physical) > 0,
            price_annual_csp_aud=None,
            price_annual_dfee_aud=None,
        )


def _parse_duration(html: str) -> float | None:
    """Extract duration from JSON field."""
    m = re.search(r'"duration"\s*:\s*"([0-9.]+)"', html)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _parse_all_atars(html: str) -> dict[str, tuple[int | None, int | None]]:
    """Parse allAtars JSON and return {campus_code: (atar_guaranteed, atar_lowest_selection_rank)}."""
    m = re.search(r'"allAtars"\s*:\s*(\{.+\}),\s*"ugRse', html, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    if not data:
        return {}
    latest_year = max(data.keys())
    result = {}
    for code, fields in data[latest_year].items():
        guaranteed = _parse_atar_float(fields.get("lowestAtarOffered", ""))
        rank = _parse_atar_float(fields.get("minSelectionRankOffered", ""))
        result[code] = (guaranteed, rank)
    return result


def _parse_atar_float(raw: str) -> int | None:
    """Parse ATAR value from string. Returns None for empty, 'NP', 'N/P', non-numeric."""
    try:
        val = float(raw.replace(",", "").strip())
        return int(round(val)) if val > 0 else None
    except (ValueError, AttributeError):
        return None


def _build_campus_links(
    campus_codes: list[str],
    atar_map: dict[str, tuple[int | None, int | None]],
    campus_map: dict[str, str],
) -> tuple[list[CampusLink], list[tuple[str, str]]]:
    """Build CampusLink list from campus codes."""
    campuses: list[CampusLink] = []
    issues: list[tuple[str, str]] = []

    for code in campus_codes:
        db_name = _CAMPUS_CODE_MAP.get(code)
        if db_name is None:
            issues.append(("campus_not_found", f"Unknown campus code '{code}'"))
            continue
        campus_id = campus_map.get(db_name)
        if campus_id is None:
            issues.append((
                "campus_not_found",
                f"Campus '{db_name}' (code '{code}') not in campus map",
            ))
            continue
        atar_guaranteed, atar_rank = atar_map.get(code, (None, None))
        is_online = (db_name == "Online")
        campuses.append(CampusLink(
            campus_id=campus_id,
            atar_guaranteed=None if is_online else atar_guaranteed,
            atar_lowest_selection_rank=None if is_online else atar_rank,
        ))

    return campuses, issues


def _classify_no_atar(url: str, name: str, html: str) -> tuple[str, str]:
    """Return (issue_type, description) for a physical-campus course with no ATAR."""
    name_lower = name.lower()
    if name_lower.startswith("diploma") or "diploma" in url.lower():
        return "diploma_entry", "Diploma — typically portfolio or work-experience entry, not ATAR-based"
    if name_lower.endswith("(honours)") or "/honours" in url.lower():
        return "honours_entry", "Honours degree — undergraduate entry via completed bachelor, not ATAR-based"
    if "portfolio" in html.lower():
        return "portfolio_entry", "Portfolio-based entry — no ATAR requirement listed"
    return "no_atar_unknown", "No ATAR found — reason could not be determined from page content"


def _infer_faculty(course_name: str) -> str | None:
    lower = course_name.lower()
    for faculty, keywords in _FACULTY_MAP:
        if any(kw in lower for kw in keywords):
            return faculty
    return None

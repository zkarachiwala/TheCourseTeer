"""RMIT University course scraper (static / httpx)."""
import asyncio
import re
import urllib.robotparser

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from db import get_campus_map, log_atar_issue
from http_client import make_client
from models import CampusLink, CourseData

SITEMAP_URL = "https://www.rmit.edu.au/sitemap.xml"
_UG_PREFIX = "/study-with-us/levels-of-study/undergraduate-study/"
# Root course URLs split to exactly 8 segments.
_COURSE_DEPTH = 8
_CONCURRENCY = 5
# Maps RMIT's location_domestic values to campus names in the DB.
_LOCATION_MAP = {"Melbourne City": "City Campus"}


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
        # Not used directly — _process_batch handles all fetching with a shared
        # httpx client. This satisfies the abstract method requirement.
        raise NotImplementedError("RmitScraper fetches via _process_batch")

    async def _process_batch(
        self,
        rp: urllib.robotparser.RobotFileParser,
        urls: list[str],
    ) -> list[tuple[str, CourseData | Exception | None]]:
        """Override to share one httpx client across all concurrent requests."""
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
                print(f"  rmit: {resp.status_code} {url}")
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
        meta = _parse_meta(soup)
        name = meta.get("product_name")
        if not name:
            return None
        mode = meta.get("learning_mode_domestic", "")
        entry_scores = _parse_entry_scores(soup)
        atar_rank, atar_guaranteed = _parse_atar(meta.get("atar"))
        campuses, issues = _resolve_campuses(
            meta.get("location_domestic", ""),
            mode,
            campus_map,
            entry_scores,
            atar_guaranteed,
            atar_rank,
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
            faculty=meta.get("college") or None,
            campuses=campuses,
            degree_type="UG",
            duration_years=_parse_duration(meta.get("duration_domestic")),
            csp_available=_parse_csp(meta.get("fees_domestic")),
            price_annual_csp_aud=None,
            price_annual_dfee_aud=None,
        )


def _parse_meta(soup: BeautifulSoup) -> dict[str, str]:
    """Extract all <meta class="elastic"> tags into a name->content dict."""
    return {
        tag["name"]: tag.get("content", "")
        for tag in soup.find_all("meta", class_="elastic")
        if tag.get("name")
    }


def _parse_entry_scores(soup: BeautifulSoup) -> list[tuple[str, int]]:
    """Parse per-campus ATARs from dd.desc.qf-lcl-entryScore.

    Each text line is: 'Point Cook campus: ATAR 60.30*'
    Returns list of (display_name, atar_lowest_selection_rank).
    """
    dd = soup.find("dd", class_="qf-lcl-entryScore")
    if not dd:
        return []
    results = []
    for line in dd.get_text(separator="\n").splitlines():
        line = line.strip().rstrip("*").strip()
        m = re.match(r"(.+?):\s+ATAR\s+(\d+(?:\.\d+)?)", line)
        if m:
            results.append((m.group(1).strip(), int(float(m.group(2)))))
    return results


def _normalise_entry_score_name(display_name: str) -> str:
    """Strip trailing ' campus' to match DB campus names (e.g. 'Point Cook campus' -> 'Point Cook')."""
    return re.sub(r"\s+campus$", "", display_name, flags=re.IGNORECASE).strip()


# Known no-ATAR categories. Add new entries here as new patterns are discovered.
# Each value is the human-readable description stored in atar_issues.description.
_NO_ATAR_CATEGORIES: dict[str, str] = {
    "honours_entry":    "Honours degree — graduate entry requires completed bachelor, not ATAR-based",
    "diploma_entry":    "Diploma — typically portfolio or work-experience entry, not ATAR-based",
    "multiple_plans":   "Multiple entry scores by study plan — ATAR varies by specialisation",
    "portfolio_entry":  "Portfolio-based entry — no ATAR requirement listed",
    "no_atar_unknown":  "No ATAR found — reason could not be determined from page content",
}


def _classify_no_atar(url: str, name: str, soup: BeautifulSoup) -> tuple[str, str]:
    """Classify why a course has no ATAR and return (issue_type, description).

    Rules are applied in priority order. The first match wins.
    Extend _NO_ATAR_CATEGORIES and add a new rule here when a new pattern is found.
    """
    page_text = soup.get_text(" ", strip=True).lower()

    if "/honours-degrees/" in url or name.lower().endswith("(honours)"):
        return "honours_entry", _NO_ATAR_CATEGORIES["honours_entry"]
    if name.lower().startswith("diploma"):
        return "diploma_entry", _NO_ATAR_CATEGORIES["diploma_entry"]
    if "multiple atar" in page_text:
        return "multiple_plans", _NO_ATAR_CATEGORIES["multiple_plans"]
    if "portfolio" in page_text:
        return "portfolio_entry", _NO_ATAR_CATEGORIES["portfolio_entry"]
    return "no_atar_unknown", _NO_ATAR_CATEGORIES["no_atar_unknown"]


def _resolve_campuses(
    location: str,
    mode: str,
    campus_map: dict[str, str],
    entry_scores: list[tuple[str, int]],
    atar_guaranteed: int | None,
    atar_rank: int | None,
) -> tuple[list[CampusLink], list[tuple[str, str]]]:
    """
    Build CampusLink list from per-campus entry scores or location_domestic fallback.

    Primary: parse dd.qf-lcl-entryScore for per-campus ATARs (lowest selection rank).
    Fallback: location_domestic meta tag + single atar meta tag applied to all campuses.
    Online delivery appended when detected in learning_mode_domestic.

    Returns (campuses, issues) where issues is a list of (issue_type, description) tuples
    to be logged by the caller.
    """
    campuses: list[CampusLink] = []
    issues: list[tuple[str, str]] = []

    if entry_scores:
        for display_name, atar in entry_scores:
            db_name = _LOCATION_MAP.get(display_name) or _normalise_entry_score_name(display_name)
            campus_id = campus_map.get(db_name)
            if campus_id is None:
                issues.append((
                    "campus_not_found",
                    f"Entry score campus '{display_name}' (normalised: '{db_name}') not in campus map",
                ))
                continue
            campuses.append(CampusLink(
                campus_id=campus_id,
                atar_lowest_selection_rank=atar,
            ))
    else:
        for raw in [loc.strip() for loc in location.split(",") if loc.strip()]:
            if raw.lower() == "online":
                continue
            db_name = _LOCATION_MAP.get(raw, raw)
            campus_id = campus_map.get(db_name)
            if campus_id is None:
                issues.append((
                    "campus_not_found",
                    f"Location '{raw}' (mapped: '{db_name}') not in campus map — no ATAR recorded",
                ))
                continue
            campuses.append(CampusLink(
                campus_id=campus_id,
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
            ))

    if "online" in mode.lower() or "online" in location.lower():
        online_id = campus_map.get("Online")
        if online_id:
            campuses.append(CampusLink(campus_id=online_id))

    return campuses, issues


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
    # Selection rank follows a comma when a guaranteed ATAR is also present.
    m = re.search(r",\s*ATAR\s+(\d+(?:\.\d+)?)", value, re.IGNORECASE)
    if m:
        return int(float(m.group(1))), guaranteed
    # Only one ATAR value present and no guaranteed — treat it as the selection rank.
    if guaranteed is None:
        m = re.search(r"\bATAR\s+(\d+(?:\.\d+)?)", value, re.IGNORECASE)
        if m:
            return int(float(m.group(1))), None
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

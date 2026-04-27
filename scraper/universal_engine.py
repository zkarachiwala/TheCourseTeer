import json
import logging
import re
import urllib.robotparser
from typing import Any

from bs4 import BeautifulSoup
from psycopg_pool import AsyncConnectionPool

from base_scraper import BaseScraper
from db import get_campus_map, get_site_config, log_atar_issue
from http_client import make_client
from models import CourseData, SiteConfig

logger = logging.getLogger(__name__)

_FACULTY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Faculty of Engineering", [
        "engineering", "electrical", "civil", "mechanical", "chemical",
        "aerospace", "biomedical", "mechatronics", "materials",
    ]),
    ("Faculty of Information Technology", [
        "information technology", "computer science", "computing", "data science",
        "cybersecurity", "artificial intelligence", "software",
    ]),
    ("Faculty of Business and Economics", [
        "business", "commerce", "economics", "accounting", "finance",
        "marketing", "management", "actuarial",
    ]),
    ("Faculty of Law", ["laws", "legal studies", "legal"]),
    ("Faculty of Medicine and Health Sciences", [
        "medicine", "medical", "nursing", "pharmacy", "physiotherapy",
        "nutrition", "dietetics", "paramedicine", "occupational therapy",
        "speech pathology", "radiation therapy", "dentistry", "biomedicine",
        "health sciences",
    ]),
    ("Faculty of Science", [
        "science", "biology", "chemistry", "physics", "mathematics",
        "statistics", "genetics", "microbiology", "neuroscience",
        "environmental science",
    ]),
    ("Faculty of Arts and Humanities", [
        "arts", "humanities", "history", "philosophy", "languages",
        "literature", "creative writing", "criminology", "politics",
        "sociology", "communications", "journalism", "psychology",
    ]),
    ("Faculty of Education", ["education", "teaching"]),
    ("Faculty of Art, Design and Architecture", [
        "design", "architecture", "fine art", "fashion", "interior design",
        "industrial design", "music", "film", "animation", "media arts",
    ]),
]


def _infer_faculty(course_name: str) -> str | None:
    name_lower = course_name.lower()
    for faculty, keywords in _FACULTY_KEYWORDS:
        if any(kw in name_lower for kw in keywords):
            return faculty
    return None


class UniversalEngine(BaseScraper):
    """
    Centralized scraping engine driven by database-stored configurations.
    Includes visual anchor fallback logic and confidence scoring.
    """

    def __init__(self, pool: AsyncConnectionPool, university_slug: str = ""):
        super().__init__(pool, university_slug)
        self._config: SiteConfig | None = None
        self._campus_map: dict[str, str] | None = None

    async def _ensure_config(self):
        from db import get_university
        if not self._university:
            self._university = await get_university(self.pool, self.slug)
        
        if not self._config:
            self._config = await get_site_config(self.pool, self.university_id)
            if not self._config:
                raise ValueError(f"No active SiteConfig for {self.slug}")
            self._campus_map = await get_campus_map(self.pool, self.university_id)

    async def discover_urls(self, rp: urllib.robotparser.RobotFileParser) -> list[str]:
        await self._ensure_config()
        disc_cfg = self._config.extraction_map.get("discovery_config", {})
        method = disc_cfg.get("method")

        urls = []
        if method == "sitemap":
            sitemap_url = disc_cfg.get("url")
            include_patterns = disc_cfg.get("include_patterns", [])
            async with make_client() as client:
                resp = await client.get(sitemap_url)
                resp.raise_for_status()
                # Basic sitemap parsing
                found = re.findall(r"<loc>(https?://[^<]+)</loc>", resp.text)
                for url in found:
                    if not include_patterns or any(p in url for p in include_patterns):
                        urls.append(url)
        elif method == "listing":
            # Implementation for listing pages if needed
            pass

        return list(set(urls))

    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        await self._ensure_config()
        self.check_robots(rp, url)

        html = None
        if self.use_cache:
            html = self.snapshots.load(
                self.university_id, url, force_refresh=self.force_refresh
            )
            if html:
                logger.info(f"Using cached snapshot for {url}")

        if not html:
            async with make_client() as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {resp.status_code}")
                    return None
                html = resp.text
                if self.use_cache:
                    self.snapshots.save(self.university_id, url, html)

        async def fetch_sub(sub_url: str) -> str:
            # Determine extension (json or html)
            ext = "json" if "json" in sub_url or "/data/" in sub_url else "html"

            if self.use_cache:
                cached = self.snapshots.load(
                    self.university_id, sub_url, ext=ext, force_refresh=self.force_refresh
                )
                if cached:
                    return cached

            # Re-use client or make new one? For simplicity make new for now
            async with make_client() as client:
                sub_resp = await client.get(sub_url)
                sub_resp.raise_for_status()
                content = sub_resp.text
                if self.use_cache:
                    self.snapshots.save(self.university_id, sub_url, content, ext=ext)
                return content

        return await self.scrape_page(
            html,
            self._config,
            url,
            campus_map=self._campus_map,
            fetch_fn=fetch_sub,
        )

    async def get_config(self, university_id: str) -> SiteConfig:
        """Fetch the active configuration for the given university."""
        config = await get_site_config(self.pool, university_id)
        if not config:
            raise ValueError(
                f"No active SiteConfig found for university_id: {university_id}"
            )
        return config

    def find_by_anchor(self, soup: BeautifulSoup, anchor_text: str) -> str | None:
        """
        Locate data based on a nearby text label (e.g., "ATAR").
        Searches for the label and returns the text of the same element (if it contains the value)
        or the next sibling/subsequent elements.
        """
        # Find all text nodes containing the anchor text
        labels = soup.find_all(string=lambda s: s and anchor_text.lower() in s.lower())

        for label_node in labels:
            # 1. Check if the label node itself contains the value (e.g., "Duration: 3 years")
            full_text = label_node.strip()
            # Heuristic: it's a value if it contains:
            # - numbers
            # - "available", "yes", "no"
            # - a colon or dash separating the label and value (e.g. "Campus: Parkville")
            is_val = (
                any(c.isdigit() for c in full_text)
                or any(k in full_text.lower() for k in ["available", "yes", "no"])
                or (":" in full_text and len(full_text.split(":", 1)[1].strip()) > 0)
                or ("-" in full_text and len(full_text.split("-", 1)[1].strip()) > 0)
            )
            if is_val:
                logger.debug(
                    f"Found value in same node as anchor '{anchor_text}': {full_text}"
                )
                return full_text

            # 2. Otherwise, look for the next non-empty string that isn't the label itself
            if hasattr(label_node, "parent"):
                curr = label_node.parent
            else:
                curr = label_node

            while curr:
                next_text = curr.find_next(string=True)
                if not next_text:
                    break
                text = next_text.strip()
                # Check if this text is not just the label or a minor variation
                if text and anchor_text.lower() not in text.lower():
                    logger.debug(
                        f"Found value in subsequent node for anchor '{anchor_text}': {text}"
                    )
                    return text
                curr = next_text

        return None

    def calculate_confidence(self, field_results: dict[str, str]) -> int:
        """
        Calculate an overall confidence score for the scraped data.
        - 100: All fields matched via primary selectors.
        - 70: Some fields matched via anchors/regex.
        - 30: Default values or failures present.
        """
        if field_results.get("name") and len(field_results) > 2:
            return 100
        return 70

    async def scrape_page(
        self,
        html: str,
        config: SiteConfig,
        url: str,
        campus_map: dict[str, str] | None = None,
        fetch_fn: Any | None = None,
    ) -> CourseData:
        """Scrape a course page using the provided configuration."""
        soup = BeautifulSoup(html, "lxml")
        field_results = {}

        # 1. Extract Name
        name_cfg = config.extraction_map.get("name", {})
        name = self._extract_field(soup, name_cfg, html, field_name="name")
        
        # Fallback: try to get name from awardTitle or advertisedTitle if regex was too specific
        if not name or name == "Unknown" or len(name) < 3:
            for key in ["awardTitle", "advertisedTitle", "award_title"]:
                m = re.search(f'"{key}"\\s*:\\s*"?([^",}}]+)"?', html)
                if m:
                    name = m.group(1).strip()
                    break
        
        # Another fallback: h1 tag
        if not name or name == "Unknown" or len(name) < 3:
            h1 = soup.select_one("h1")
            if h1:
                name = h1.get_text(strip=True)
        
        # Last resort fallback: from URL slug
        if not name or name == "Unknown" or len(name) < 3:
            name = url.split("/")[-1].replace("-", " ").title()
            
        if name:
            field_results["name"] = name

        # 2. Extract Duration
        dur_cfg = config.extraction_map.get("duration", {})
        duration_str = self._extract_field(soup, dur_cfg, html, field_name="duration")
        
        # Fallback: try to find duration in full HTML if selector/regex failed
        if not duration_str:
            m = re.search(r'"duration"\s*:\s*"?([^",}]+)"?', html)
            if m:
                duration_str = m.group(1)

        duration = self._parse_duration(duration_str)
        
        # Fallback: try to infer from credit points (360 CP = 3 years, 240 CP = 2 years, etc.)
        if not duration:
            m = re.search(r'"totalCreditPoints"\s*:\s*(\d+)', html)
            if m:
                cp = int(m.group(1))
                if cp > 0:
                    duration = cp / 120.0
                    logger.debug(f"Inferred duration {duration} from {cp} credit points")

        if duration:
            field_results["duration"] = str(duration)

        # 3. Extract ATAR
        atar_cfg = config.extraction_map.get("atar", {})
        atar_str = self._extract_field(soup, atar_cfg, html, field_name="atar")
        atar_guaranteed, atar_rank = self._parse_atar(atar_str)
        if atar_guaranteed or atar_rank:
            field_results["atar"] = atar_str

        # DISCARD NON-COURSE PAGES (e.g. info pages, contact pages, study areas)
        # If it doesn't have credit points AND doesn't have a duration, it's probably not a course
        if not duration and '"totalCreditPoints":0' in html.replace(" ", ""):
            logger.warning(f"Discarding potential non-course page: {url}")
            return None
        
        # If the name is a known study area or major name from the sitemap
        if any(k in name.lower() for k in ["contact us", "how to apply", "timetables", "director and staff"]):
             logger.warning(f"Discarding information page: {name} from {url}")
             return None

        # 4. Extract Fees
        fees_cfg = config.extraction_map.get("fees", {})
        anchor = fees_cfg.get("anchor")
        csp_available = False
        if anchor:
            anchor_val = self.find_by_anchor(soup, anchor)
            if anchor_val:
                csp_available = any(
                    k in anchor_val.lower()
                    for k in ["commonwealth", "csp", "supported", "$"]
                )
                field_results["fees"] = anchor_val

        if not csp_available:
            fees_str = self._extract_field(soup, fees_cfg, html, field_name="fees")
            if fees_str:
                field_results["fees"] = fees_str
                csp_available = any(
                    k in fees_str.lower()
                    for k in ["commonwealth", "csp", "supported", "$"]
                )
                if not csp_available and "FeeDomesticCSP" in fees_cfg.get("regex", ""):
                    csp_available = True

        # 5. Admissions Codes
        adm_cfg = config.extraction_map.get("admissions_codes", {})
        adm_codes = self.extract_admissions_codes(soup, adm_cfg)
        if adm_codes:
            field_results["admissions_codes"] = ",".join(adm_codes)

        # 6. Location / Campuses
        loc_cfg = config.extraction_map.get("location", {})
        location_raw = self._extract_field(soup, loc_cfg, html, field_name="location")

        campuses = []
        if location_raw:
            # Parse multiple locations if present (comma-separated or JSON list)
            location_list = []
            if location_raw.startswith("[") and location_raw.endswith("]"):
                try:
                    location_list = json.loads(location_raw)
                except:
                    location_list = [location_raw]
            else:
                # Common separators: comma, semicolon, or "and"
                raw_list = re.split(r",|;| and ", location_raw, flags=re.IGNORECASE)
                # Clean each location - remove parentheticals like [Full-time] or (Parkville)
                location_list = []
                for loc in raw_list:
                    cleaned = re.sub(r"\[[^\]]+\]|\([^\)]+\)", "", loc).strip()
                    if cleaned:
                        location_list.append(cleaned)

            location_mapping = loc_cfg.get("mapping", {})

            from models import CampusLink

            for loc in location_list:
                # Map location to campus_id
                campus_id = None
                
                # 1. Try explicit mapping from config
                if location_mapping and loc in location_mapping:
                    campus_id = location_mapping[loc]
                
                # 2. Try exact name match from pre-loaded campus_map
                if not campus_id and self._campus_map:
                    # Case-insensitive search in campus_map (name -> id)
                    loc_lower = loc.lower()
                    for name, cid in self._campus_map.items():
                        if loc_lower == name.lower():
                            campus_id = cid
                            break
                            
                # 3. Fallback to raw string (though this will fail DB constraints)
                if not campus_id:
                    logger.warning(f"Could not resolve campus name '{loc}' to a UUID for {self.slug}")
                    campus_id = loc

                campuses.append(
                    CampusLink(
                        campus_id=campus_id,
                        atar_guaranteed=atar_guaranteed,
                        atar_lowest_selection_rank=atar_rank,
                        admissions_codes=list(adm_codes),
                        confidence_score=70,
                    )
                )

        # 7. Follow URLs (e.g. for La Trobe detail JSONs)
        follow_cfg = config.extraction_map.get("follow_urls")
        if follow_cfg and fetch_fn:
            regex = follow_cfg.get("regex")
            if regex:
                # Find all matching URLs in the HTML
                matches = re.findall(regex, html)
                logger.debug(f"found {len(matches)} potential follow URLs with regex '{regex}'")
                for sub_url in matches:
                    if not sub_url.startswith("http"):
                        sub_url = (
                            config.base_url.rstrip("/") + "/" + sub_url.lstrip("/")
                        )

                    logger.debug(f"following URL: {sub_url}")
                    try:
                        sub_html = await fetch_fn(sub_url)
                        logger.debug(f"fetched sub_html, length={len(sub_html)}")
                        # Extract more data from the sub-page
                        # For La Trobe, we want VTAC codes from the detail JSON
                        sub_adm_codes = self.extract_admissions_codes(
                            BeautifulSoup(sub_html, "lxml"), adm_cfg
                        )
                        logger.debug(f"extracted {len(sub_adm_codes)} admissions codes from sub-page")
                        if sub_adm_codes:
                            # Heuristic: try to match sub_url to a campus
                            # La Trobe URLs have campus code in them, e.g. /domestic/bu/
                            matched_campus = None
                            for campus in campuses:
                                if f"/{campus.campus_id.lower()}/" in sub_url.lower():
                                    matched_campus = campus
                                    break

                            if matched_campus:
                                matched_campus.admissions_codes.extend(sub_adm_codes)
                                matched_campus.admissions_codes = sorted(
                                    list(set(matched_campus.admissions_codes))
                                )
                            else:
                                # If no specific campus match, add to all
                                for campus in campuses:
                                    campus.admissions_codes.extend(sub_adm_codes)
                                    campus.admissions_codes = sorted(
                                        list(set(campus.admissions_codes))
                                    )
                    except Exception as e:
                        logger.error(f"Failed to fetch followed URL {sub_url}: {e}")

        if adm_codes or any(c.admissions_codes for c in campuses):
            # Just for field_results tracking
            field_results["admissions_codes"] = "found"

        confidence = self.calculate_confidence(field_results)

        # FINAL DATA QUALITY CHECKS
        if not name or name == "Unknown" or len(name) < 3:
            logger.warning(f"Discarding result with invalid name '{name}' from {url}")
            return None

        # Record ATAR issue if missing for UG courses
        if not atar_guaranteed and not atar_rank:
            try:
                # We need self._run_id from base_scraper
                if hasattr(self, "_run_id") and self._run_id:
                    await log_atar_issue(
                        self.pool,
                        config.university_id,
                        self._run_id,
                        name,
                        url,
                        "missing_atar",
                        "No ATAR found via primary selectors or anchors"
                    )
            except Exception as e:
                logger.error(f"Failed to record ATAR issue: {e}")

        return CourseData(
            university_id=config.university_id,
            name=name,
            source_url=url,
            faculty=_infer_faculty(name) if name else None,
            campuses=campuses,
            degree_type="UG",
            duration_years=duration,
            csp_available=csp_available,
            confidence_score=confidence,
        )

    def _extract_field(
        self,
        soup: BeautifulSoup,
        field_cfg: dict,
        full_html: str | None = None,
        field_name: str | None = None,
    ) -> str | None:
        """Helper to extract a field based on selector, attr, anchor, or regex."""
        val = None

        # 1. Try JSON-LD first if specified
        json_ld_path = field_cfg.get("json_ld")
        if json_ld_path:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    content = script.string or script.text
                    if not content:
                        continue
                    data = json.loads(content)
                    objs = data if isinstance(data, list) else [data]

                    keys = json_ld_path.split(".")
                    for obj in objs:
                        curr = obj
                        if keys[0].lower() == str(curr.get("@type", "")).lower():
                            keys_to_use = keys[1:]
                        else:
                            keys_to_use = keys

                        for k in keys_to_use:
                            if isinstance(curr, dict) and k in curr:
                                curr = curr[k]
                            else:
                                curr = None
                                break
                        if curr:
                            val = str(curr)
                            break
                    if val:
                        break
                except (json.JSONDecodeError, TypeError):
                    continue

        # 2. Try selector
        if not val:
            selector = field_cfg.get("selector")
            if selector:
                key_text = field_cfg.get("key")
                if key_text:
                    rows = soup.select(selector)
                    for row in rows:
                        cells = row.find_all(["th", "td"])
                        if (
                            len(cells) >= 2
                            and key_text.lower() in cells[0].get_text(strip=True).lower()
                        ):
                            val = cells[1].get_text(" ", strip=True)
                            break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        attr = field_cfg.get("attr")
                        val = elem.get(attr) if attr else elem.get_text(strip=True)

                if val:
                    logger.debug(f"Selector '{selector}' (key={key_text}) found: {val}")

        # 3. Fallback to anchor
        if not val:
            anchor = field_cfg.get("anchor")
            if anchor:
                val = self.find_by_anchor(soup, anchor)
                
        # 4. Apply regex if provided
        regex = field_cfg.get("regex")
        if regex:
            # If we don't have a value yet, try running regex on the full HTML
            # BUT if we have an anchor value, we apply regex to THAT to refine it
            target_text = val if val else full_html
            if target_text:
                logger.debug(
                    f"Applying regex '{regex}' to text length {len(target_text)}"
                )
                m = re.search(regex, target_text, re.IGNORECASE)
                if m:
                    try:
                        # Prefer captured group if available (e.g. just the name, 
                        # or the specific part of ATAR string if the regex defined it)
                        val = m.group(1)
                        logger.debug(f"Regex match result (group 1) for {field_name}: {val}")
                    except IndexError:
                        # No capture group, use group(0) OR full context for certain fields
                        if field_name in ["atar", "duration", "fees"]:
                            # Return the full target_text to keep context for _parse methods
                            # like 'Guaranteed' vs 'Lowest'
                            val = target_text
                            logger.debug(f"Regex matched, returning full context for {field_name}")
                        else:
                            val = m.group(0)
                            logger.debug(f"Regex match result (group 0) for {field_name}: {val}")
                elif val:
                    # If regex was supposed to refine a value but failed, clear it
                    val = None
                    logger.debug(f"Regex did not match for {field_name}")

        if val and isinstance(val, str):
            # Unescape common JSON escapes if found (e.g. \/ -> /)
            # We do a case-insensitive check for common escapes
            if "\\" in val:
                # Handle common JSON string escapes
                escapes = {
                    "\\/": "/",
                    "\\\"": "\"",
                    "\\\\": "\\",
                    "\\b": "\b",
                    "\\f": "\f",
                    "\\n": "\n",
                    "\\r": "\r",
                    "\\t": "\t"
                }
                for esc, sub in escapes.items():
                    if esc in val:
                        val = val.replace(esc, sub)
                
                # Also handle potential unicode escapes if needed
                if "\\u" in val:
                    try:
                        # Use codecs for more robust unicode unescaping
                        import codecs
                        val = codecs.decode(val, 'unicode_escape')
                    except Exception as e:
                        logger.warning(f"Failed to unescape unicode in {field_name}: {e}")

            # Final cleanup: strip any trailing quotes that might have been caught by flexible regex
            val = val.strip().strip('"').strip("'").strip()

        return val

    def _parse_duration(self, text: str | None) -> float | None:
        if not text:
            return None
        logger.debug(f"_parse_duration: text length={len(text)}")
        m = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(m.group(1)) if m else None

    def _parse_atar(self, text: str | None) -> tuple[int | None, int | None]:
        """
        Return (atar_guaranteed, atar_lowest_selection_rank) from text.
        """
        if not text:
            return None, None

        guaranteed = None
        rank = None

        # Look for numbers, but filter out years (e.g. 2024, 2025, 2026)
        # ATARs are always <= 99.95
        m = re.findall(r"(\d{2,4}(?:\.\d+)?)", text)
        if not m:
            return None, None

        vals = []
        for n in m:
            val = float(n)
            # If it's a 4-digit integer starting with 20, it's likely a year
            if 1900 <= val <= 2100:
                continue
            vals.append(int(val))

        if not vals:
            return None, None

        lower_text = text.lower()
        logger.debug(f"_parse_atar: text='{text}', vals={vals}, lower_text='{lower_text}'")
        if any(k in lower_text for k in ["guarantee", "guaranteed", "minimum", "aspire"]):
            guaranteed = vals[0]
            if len(vals) > 1:
                rank = vals[1]
        elif any(k in lower_text for k in ["selection rank", "rank", "lowest", "minselectionrankoffered"]):
            rank = vals[0]
            if len(vals) > 1:
                guaranteed = vals[1]
        else:
            # Default to selection rank if no keywords
            rank = vals[0]
            if len(vals) > 1:
                guaranteed = vals[1]

        return guaranteed, rank

    def extract_admissions_codes(self, soup: BeautifulSoup, config: dict) -> list[str]:
        """Extract admissions codes (VTAC, UAC, etc.) based on anchor or regex."""
        results = set()
        anchor = config.get("anchor")
        regex = config.get("regex")

        if anchor:
            label_text = self.find_by_anchor(soup, anchor)
            if label_text:
                if regex:
                    matches = re.findall(regex, label_text)
                    results.update(matches)
                else:
                    results.add(label_text)

        if not results and regex:
            text = soup.get_text(" ")
            matches = re.findall(regex, text)
            results.update(matches)

        return sorted(list(results))

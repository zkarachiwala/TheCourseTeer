import json
import logging
import re
import urllib.robotparser
from typing import Any

from bs4 import BeautifulSoup
from psycopg_pool import AsyncConnectionPool

from base_scraper import BaseScraper
from db import get_campus_map, get_faculties, get_site_config, log_atar_issue
from http_client import make_client
from models import CourseData, SiteConfig

logger = logging.getLogger(__name__)


class UniversalEngine(BaseScraper):
    """
    Centralized scraping engine driven by database-stored configurations.
    Includes visual anchor fallback logic and confidence scoring.
    """

    def __init__(self, pool: AsyncConnectionPool, university_slug: str = ""):
        super().__init__(pool, university_slug)
        self._config: SiteConfig | None = None
        self._campus_name_map: dict[str, str] | None = None
        self._campus_code_map: dict[str, str] | None = None
        self._faculties: list[tuple[str, list[str]]] | None = None

    async def _ensure_config(self):
        from db import get_university
        if not self._university:
            self._university = await get_university(self.pool, self.slug)
        
        if not self._config:
            self._config = await get_site_config(self.pool, self.university_id)
            if not self._config:
                raise ValueError(f"No active SiteConfig for {self.slug}")
            self._campus_name_map, self._campus_code_map = await get_campus_map(self.pool, self.university_id)
            self._faculties = await get_faculties(self.pool)

    def _infer_faculty(self, name: str) -> str | None:
        if not self._faculties or not name:
            return None
        name_lower = name.lower()
        for faculty, keywords in self._faculties:
            if any(kw.lower() in name_lower for kw in keywords):
                return faculty
        return None

    def _infer_degree_type(self, name: str) -> str:
        name_lower = name.lower()
        if any(k in name_lower for k in ["master", "doctor", "graduate certificate", "graduate diploma", "postgraduate", "juris doctor"]):
            return "PG"
        return "UG"

    def _should_discard_by_meta(self, soup: BeautifulSoup, config: SiteConfig) -> bool:
        """Check if page should be discarded based on meta tags in config."""
        discard_cfg = config.extraction_map.get("discard_meta")
        if not discard_cfg:
            return False
            
        # discard_cfg is a list of dicts: {"name": "...", "content": "..."}
        if not isinstance(discard_cfg, list):
            discard_cfg = [discard_cfg]
            
        for rule in discard_cfg:
            name = rule.get("name")
            content = rule.get("content")
            
            meta = soup.find("meta", {"name": name})
            if meta:
                meta_content = meta.get("content")
                if content is None: # Just check for presence
                    return True
                if meta_content == content:
                    return True
        return False

    def _is_valid_course(self, name: str, url: str) -> bool:
        """
        Strict validation: real degrees start with specific academic titles.
        Discards hub pages, majors, and study areas.
        """
        if not name or name.lower() == "unknown" or len(name) <= 3:
            return False
            
        name_lower = name.lower()
        
        # Valid prefixes for degrees
        valid_prefixes = [
            "bachelor", "diploma", "associate degree", "undergraduate certificate", 
            "advanced diploma", "master", "doctor", "graduate certificate", 
            "graduate diploma", "juris doctor", "honours"
        ]
        
        # Check if it starts with any valid prefix
        if any(name_lower.startswith(p) for p in valid_prefixes):
            return True
            
        # Exception: if it clearly contains "degree" in the name
        if " degree" in name_lower or " course" in name_lower:
            return True

        logger.warning(f"Discarding potential non-course page: '{name}' from {url}")
        return False

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
        # 1. Primary Fetch: HTML Page (Main target for ATAR/Duration)
        if self.use_cache:
            html = self.snapshots.load(
                self.university_id, url, ext="html", force_refresh=self.force_refresh
            )
            if html:
                logger.info(f"Using cached HTML snapshot for {url}")

        if not html:
            async with make_client() as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {resp.status_code}")
                    return None
                html = resp.text
                if self.use_cache:
                    # Explicitly save as HTML
                    self.snapshots.save(self.university_id, url, html, ext="html")

        async def fetch_sub(sub_url: str) -> str:
            # Determine extension (json or html)
            ext = "json" if "json" in sub_url or "/data/" in sub_url else "html"

            if self.use_cache:
                cached = self.snapshots.load(
                    self.university_id, sub_url, ext=ext, force_refresh=self.force_refresh
                )
                if cached:
                    return cached

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
            campus_map=self._campus_name_map,
            code_map=self._campus_code_map,
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

    def _preprocess_html(self, html: str, config: SiteConfig) -> str:
        """Apply generic cleanup regexes to the raw HTML before parsing."""
        cleanup_regexes = config.extraction_map.get("cleanup_regexes", [])
        if not cleanup_regexes:
            return html
        
        cleaned = html
        for regex in cleanup_regexes:
            try:
                cleaned = re.sub(regex, '', cleaned, flags=re.DOTALL)
            except Exception as e:
                logger.error(f"Cleanup regex failure: {e}")
        return cleaned

    def _extract_json_map(self, html: str, field_cfg: dict) -> dict:
        """Generic logic to extract a JSON block from text based on a regex."""
        json_regex = field_cfg.get("json_regex")
        if not json_regex:
            return {}
        
        m = re.search(json_regex, html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                # If it's a nested structure (like La Trobe's year-based map),
                # allow the config to specify a 'json_path'
                json_path = field_cfg.get("json_path")
                if json_path and isinstance(data, dict):
                    if json_path == "latest_key":
                        # Specialized: get the most recent year/key
                        keys = sorted(data.keys(), reverse=True)
                        if keys:
                            data = data[keys[0]]
                    else:
                        # Standard path like "data.atars"
                        for k in json_path.split("."):
                            data = data.get(k, {})
                return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"Generic JSON extraction failure: {e}")
        return {}

    def find_by_anchor(self, soup: BeautifulSoup, anchor_text: str) -> str | None:
        """
        Locate data based on a nearby text label (e.g., "ATAR").
        Searches for the label and returns the text of the same element (if it contains the value)
        or the next sibling/subsequent elements.
        """
        # Find all text nodes containing the anchor text
        labels = soup.find_all(string=lambda s: s and anchor_text.lower() in s.lower())

        for label_node in labels:
            full_text = label_node.strip()
            # Heuristic: it's a value if it contains:
            # - numbers, "available", "yes", "no", or separators
            is_val = (
                any(c.isdigit() for c in full_text)
                or any(k in full_text.lower() for k in ["available", "yes", "no"])
                or (":" in full_text and len(full_text.split(":", 1)[1].strip()) > 0)
                or ("-" in full_text and len(full_text.split("-", 1)[1].strip()) > 0)
            )
            if is_val:
                return full_text

            if hasattr(label_node, "parent"):
                curr = label_node.parent
            else:
                curr = label_node

            while curr:
                next_text = curr.find_next(string=True)
                if not next_text:
                    break
                text = next_text.strip()
                if text and anchor_text.lower() not in text.lower():
                    return text
                curr = next_text

        return None

    def calculate_confidence(self, field_results: dict[str, str]) -> int:
        if field_results.get("name") and len(field_results) > 2:
            return 100
        return 70

    async def scrape_page(
        self,
        html: str,
        config: SiteConfig,
        url: str,
        campus_map: dict[str, str] | None = None,
        code_map: dict[str, str] | None = None,
        fetch_fn: Any | None = None,
    ) -> CourseData | None:
        """Scrape a course page using the provided configuration."""
        
        # 0. Pre-process HTML (e.g. remove noise)
        clean_html = self._preprocess_html(html, config)
        soup = BeautifulSoup(clean_html, "lxml")
        
        # 0.1 Meta-tag Discard Logic
        if self._should_discard_by_meta(soup, config):
            logger.info(f"Discarding hub/category page by meta tag: {url}")
            return None

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
            
        if not name or not self._is_valid_course(name, url):
            return None

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
        atar_str = self._extract_field(soup, atar_cfg, clean_html, field_name="atar")
        atar_guaranteed, atar_rank = self._parse_atar(atar_str)

        # Generic JSON Fallback (e.g. for La Trobe allAtars)
        atar_json_map = self._extract_json_map(clean_html, atar_cfg)

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
        fees_str = self._extract_field(soup, fees_cfg, clean_html, field_name="fees")
        csp_available = False
        if fees_str:
            field_results["fees"] = fees_str
            csp_available = any(
                k in fees_str.lower()
                for k in ["commonwealth", "csp", "supported", "$"]
            )

        # 5. Admissions Codes
        adm_cfg = config.extraction_map.get("admissions_codes", {})
        adm_codes = self.extract_admissions_codes(soup, adm_cfg)

        # 6. Location / Campuses
        loc_cfg = config.extraction_map.get("location", {})
        location_raw = self._extract_field(soup, loc_cfg, clean_html, field_name="location")

        campuses = []
        if location_raw:
            location_list = []
            if location_raw.startswith("[") and location_raw.endswith("]"):
                try:
                    location_list = json.loads(location_raw)
                except:
                    location_list = [location_raw]
            else:
                raw_list = re.split(r",|;| and ", location_raw, flags=re.IGNORECASE)
                location_list = []
                for loc in raw_list:
                    cleaned = re.sub(r"\[[^\]]+\]|\([^\)]+\)", "", loc).strip()
                    if cleaned:
                        location_list.append(cleaned)

            location_mapping = loc_cfg.get("mapping", {})

            from models import CampusLink

            for loc in location_list:
                campus_id = None
                if location_mapping and loc in location_mapping:
                    campus_id = location_mapping[loc]
                
                if not campus_id and campus_map:
                    loc_lower = loc.lower()
                    if loc_lower in campus_map:
                        campus_id = campus_map[loc_lower]
                            
                if not campus_id and code_map:
                    loc_lower = loc.lower()
                    if loc_lower in code_map:
                        campus_id = code_map[loc_lower]

                if not campus_id:
                    campus_id = loc

                # Determine ATAR for THIS specific campus
                this_atar_guaranteed = atar_guaranteed
                this_atar_rank = atar_rank
                
                if atar_json_map and code_map:
                    codes_for_this_campus = [c.upper() for c, cid in code_map.items() if cid == campus_id]
                    for c in codes_for_this_campus:
                        if c in atar_json_map:
                            val = atar_json_map[c].get("minSelectionRankOffered")
                            if val and val not in ["N/A", "N/P", "NP", "RC"]:
                                try:
                                    this_atar_rank = int(float(val))
                                except:
                                    pass
                            
                            g_val = atar_json_map[c].get("aspireMinimumATAR")
                            if g_val and g_val not in ["N/A", "N/P", "NP", "RC"]:
                                try:
                                    this_atar_guaranteed = int(float(g_val))
                                except:
                                    pass
                            break

                campuses.append(
                    CampusLink(
                        campus_id=campus_id,
                        atar_guaranteed=this_atar_guaranteed,
                        atar_lowest_selection_rank=this_atar_rank,
                        admissions_codes=[], 
                        confidence_score=70,
                    )
                )

        # 7. Follow URLs (e.g. for detail JSONs)
        follow_cfg = config.extraction_map.get("follow_urls")
        if follow_cfg and fetch_fn:
            regex = follow_cfg.get("regex")
            if regex:
                matches = re.findall(regex, clean_html)
                for sub_url in matches:
                    if not sub_url.startswith("http"):
                        sub_url = config.base_url.rstrip("/") + "/" + sub_url.lstrip("/")

                    try:
                        sub_content = await fetch_fn(sub_url)
                        # Generic sub-content extraction
                        sub_adm_codes = self.extract_admissions_codes(
                            BeautifulSoup(sub_content, "lxml"), adm_cfg
                        )
                        
                        # Generic duration/cp extraction from sub-content
                        sub_duration = None
                        m_sub_dur = re.search(r'"duration"\s*:\s*"?([^",}]+)"?', sub_content)
                        if m_sub_dur:
                            sub_duration = self._parse_duration(m_sub_dur.group(1))
                        
                        # PRIORITY: totalCreditPoints from JSON is extremely reliable
                        m_sub_cp = re.search(r'"totalCreditPoints"\s*:\s*(\d+)', sub_content)
                        if m_sub_cp:
                            cp = int(m_sub_cp.group(1))
                            if cp > 0:
                                inferred = cp / 120.0
                                # If JSON duration says 5.0 and HTML said 1.0, 5.0 wins.
                                if not sub_duration or (0.5 <= inferred <= 10.0 and inferred > sub_duration):
                                    sub_duration = inferred

                        if sub_adm_codes or sub_duration:
                            matched_campus = None
                            for campus in campuses:
                                if code_map:
                                    target_codes = [c for c, cid in code_map.items() if cid == campus.campus_id]
                                    if any(f"/{tc}/" in sub_url.lower() for tc in target_codes):
                                        matched_campus = campus
                                        break

                            if matched_campus:
                                if sub_adm_codes:
                                    matched_campus.admissions_codes.extend(sub_adm_codes)
                                    matched_campus.admissions_codes = sorted(list(set(matched_campus.admissions_codes)))
                                if sub_duration:
                                    # Update global duration if sub-duration is superior
                                    if not duration or (0.5 <= sub_duration <= 10.0 and sub_duration > duration):
                                        duration = sub_duration
                            else:
                                for campus in campuses:
                                    if sub_adm_codes:
                                        campus.admissions_codes.extend(sub_adm_codes)
                                        campus.admissions_codes = sorted(list(set(campus.admissions_codes)))
                                if sub_duration:
                                    if not duration or (0.5 <= sub_duration <= 10.0 and sub_duration > duration):
                                        duration = sub_duration
                    except Exception as e:
                        logger.error(f"Failed to fetch followed URL {sub_url}: {e}")

        if adm_codes or any(c.admissions_codes for c in campuses):
            field_results["admissions_codes"] = "found"

        if duration:
            field_results["duration"] = str(duration)

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

        faculty = self._infer_faculty(name)
        degree_type = self._infer_degree_type(name)

        return CourseData(
            university_id=config.university_id,
            name=name,
            source_url=url,
            faculty=faculty,
            campuses=campuses,
            degree_type=degree_type,
            duration_years=duration,
            csp_available=csp_available,
            confidence_score=confidence,
        )

    def _extract_field(
        self,
        soup: BeautifulSoup,
        field_cfg: dict,
        full_text: str | None = None,
        field_name: str | None = None,
    ) -> str | None:
        val = None

        # 1. Selector
        selector = field_cfg.get("selector")
        if selector:
            key_text = field_cfg.get("key")
            if key_text:
                rows = soup.select(selector)
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    if len(cells) >= 2 and key_text.lower() in cells[0].get_text(strip=True).lower():
                        val = cells[1].get_text(" ", strip=True)
                        break
            else:
                elem = soup.select_one(selector)
                if elem:
                    attr = field_cfg.get("attr")
                    val = elem.get(attr) if attr else elem.get_text(strip=True)

        # 2. Anchor
        if not val:
            anchor = field_cfg.get("anchor")
            if anchor:
                val = self.find_by_anchor(soup, anchor)
                
        # 3. Regex
        regex = field_cfg.get("regex")
        if regex:
            target_text = val if val else full_text
            if target_text:
                m = re.search(regex, target_text, re.IGNORECASE)
                if m:
                    try:
                        val = m.group(1)
                    except IndexError:
                        val = m.group(0)

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
        
        # LOOK FOR CONTEXT: number followed by year/month/wk keywords
        # This prevents picking up AQF levels (like 'Level 9') or random numbers.
        m = re.search(r"(\d+(?:\.\d+)?)\s*(year|yr|month|mon|week|wk)", text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            
            if "month" in unit or "mon" in unit:
                val = val / 12.0
            elif "week" in unit or "wk" in unit:
                val = val / 52.0
                
            # SANITY CHECK: Durations are usually between 0.2 and 10 years.
            if 0.2 <= val <= 10.0:
                return val
        
        # Fallback for plain numbers ONLY if they are very small (typical for years)
        m_plain = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", text)
        if m_plain:
            val = float(m_plain.group(1))
            if 0.5 <= val <= 8.0:
                return val
                
        return None

    def _parse_atar(self, text: str | None) -> tuple[int | None, int | None]:
        if not text:
            return None, None
        
        # Look for numbers while keeping track of their context
        # ATARs are almost always 30.00 to 99.95
        matches = list(re.finditer(r"(\d{2}(?:\.\d+)?)", text))
        if not matches:
            return None, None
            
        guaranteed = None
        rank = None
        
        for m in matches:
            val_str = m.group(1)
            val = int(float(val_str))
            
            # Filter out years and invalid ranks
            if not (30 <= val <= 100):
                continue
                
            # Check context: 30 chars before the match
            start = max(0, m.start() - 30)
            context = text[start:m.start()].lower()
            
            if any(k in context for k in ["guarantee", "minimum", "aspire"]):
                if guaranteed is None: guaranteed = val
            elif any(k in context for k in ["rank", "lowest", "offered"]):
                if rank is None: rank = val
            else:
                # No clear keyword, assign to the first empty slot (prefer rank)
                if rank is None: rank = val
                elif guaranteed is None: guaranteed = val
        
        return guaranteed, rank

    def extract_admissions_codes(self, soup: BeautifulSoup, config: dict) -> list[str]:
        results = set()
        anchor = config.get("anchor")
        regex = config.get("regex")
        if anchor:
            label_text = self.find_by_anchor(soup, anchor)
            if label_text and regex:
                results.update(re.findall(regex, label_text))
        if not results and regex:
            results.update(re.findall(regex, soup.get_text(" ")))
        return sorted(list(results))

import json
import logging
import os
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
        STRICT: Only allow Bachelor degrees as per user instruction.
        """
        if not name or name.lower() == "unknown" or len(name) <= 3:
            return False
            
        name_lower = name.lower()

        # DISCARD CAMPUS NAMES AS COURSE NAMES
        # (Fix for Swinburne "Prahran" ghost course)
        campuses = ["prahran", "hawthorn", "croydon", "wantirna", "bundoora", "bendigo", "melbourne city", "albury-wodonga", "mildura", "shepparton"]
        if name_lower in campuses:
            logger.warning(f"Discarding course name that matches campus: '{name}' from {url}")
            return False

        # Undergraduate filter
        filter_level = os.getenv("COURSE_LEVEL_FILTER", "UG")
        if filter_level == "UG":
            pg_keywords = ["master", "doctor", "juris doctor", "graduate certificate", "graduate diploma", "postgraduate"]
            if any(k in name_lower for k in pg_keywords):

                # Exception: "Doctor of Medicine" is technically a graduate degree but often treated as a target.
                # However, following the "undergraduate only" mandate strictly:
                logger.debug(f"Discarding postgraduate course: {name}")
                return False
        
        # Discard obvious non-undergraduate markers
        if any(k in name_lower for k in ["master", "doctor", "graduate certificate", "graduate diploma", "juris doctor", "postgraduate"]):
            return False

        # STRICT: Must contain 'bachelor'
        if "bachelor" in name_lower:
            return True

        logger.warning(f"Discarding non-bachelor or non-course page: '{name}' from {url}")
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
            listing_url = disc_cfg.get("url")
            if not listing_url:
                return []
            
            async def fetch_listing(url):
                if url.startswith("file://"):
                    path = url.replace("file://", "")
                    # Resolve relative to project root if needed
                    if not os.path.isabs(path):
                        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
                    with open(path, 'r') as f:
                        return f.read(), "application/json"
                
                try:
                    async with make_client() as client:
                        resp = await client.get(url)
                        if resp.status_code == 403:
                            raise PermissionError("403 Forbidden")
                        resp.raise_for_status()
                        return resp.text, resp.headers.get("Content-Type", "")
                except Exception as e:
                    logger.warning(f"Standard fetch failed for listing {url}, trying browser: {e}")
                    from browser import browser_context
                    async with browser_context() as ctx:
                        page = await ctx.new_page()
                        await page.goto(url, wait_until="networkidle")
                        content = await page.content()
                        # Browser fetch might return HTML even for JSON if it's rendered
                        # but often it just shows the JSON text.
                        text = await page.evaluate("() => document.body.innerText")
                        return text, "application/json"

            content, content_type = await fetch_listing(listing_url)
            
            # If the listing itself is JSON (like Deakin)
            if "application/json" in content_type or listing_url.endswith("json") or "search-json" in listing_url:
                try:
                    data = json.loads(content)
                except:
                    # If it's HTML wrapped JSON (browser fallback)
                    try:
                        data = json.loads(re.search(r'(\{.*\})', content, re.DOTALL).group(1))
                    except:
                        data = {}
                
                results = data.get("response", {}).get("resultPacket", {}).get("results", [])
                if results:
                    for r in results:
                        u = r.get("liveUrl") or r.get("url")
                        if u:
                            if not u.startswith("http"):
                                u = "https:" + u if u.startswith("//") else self._config.base_url.rstrip("/") + u
                            urls.append(u)
                            if self.use_cache:
                                self.snapshots.save(self.university_id, u, json.dumps(r), ext="json")
                else:
                    found = re.findall(r'"(https?://[^"]+)"', content)
                    urls.extend(found)

        return list(set(urls))

    async def scrape_url(
        self, rp: urllib.robotparser.RobotFileParser, url: str
    ) -> CourseData | None:
        await self._ensure_config()
        self.check_robots(rp, url)

        content = None
        # 1. Primary Fetch
        if self.use_cache:
            ext = "json" if self._config.extraction_map.get("source_type") == "json" else "html"
            content = self.snapshots.load(
                self.university_id, url, ext=ext, force_refresh=self.force_refresh
            )
            if content:
                logger.info(f"Using cached {ext} snapshot for {url}")

        if not content:
            async with make_client() as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {resp.status_code}")
                    return None
                content = resp.text
                if self.use_cache:
                    ext = "json" if self._config.extraction_map.get("source_type") == "json" else "html"
                    self.snapshots.save(self.university_id, url, content, ext=ext)

        if self._config.extraction_map.get("source_type") == "json":
            try:
                data = json.loads(content)
                return await self.scrape_json_data(data, self._config, url)
            except Exception as e:
                logger.error(f"Failed to parse JSON from {url}: {e}")
                return None

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
                sub_content = sub_resp.text
                if self.use_cache:
                    self.snapshots.save(self.university_id, sub_url, sub_content, ext=ext)
                return sub_content

        return await self.scrape_page(
            content,
            self._config,
            url,
            campus_map=self._campus_name_map,
            code_map=self._campus_code_map,
            fetch_fn=fetch_sub,
        )

    async def scrape_json_data(
        self,
        data: dict | list,
        config: SiteConfig,
        url: str
    ) -> CourseData | None:
        """Scrape a course from a JSON object using the provided configuration."""
        
        if isinstance(data, list):
            if not data: return None
            data = data[0]

        field_results = {}

        # 1. Name
        name_cfg = config.extraction_map.get("name", {})
        name = self._extract_field(None, name_cfg, json_data=data, field_name="name")
        if not name or not self._is_valid_course(name, url):
            return None
        field_results["name"] = name

        # 2. Duration
        dur_cfg = config.extraction_map.get("duration", {})
        duration_str = self._extract_field(None, dur_cfg, json_data=data, field_name="duration")
        duration = self._parse_duration(duration_str)
        if duration:
            field_results["duration"] = str(duration)

        # 2.1 Degree Type
        deg_cfg = config.extraction_map.get("degree_type", {})
        degree_type = self._extract_field(None, deg_cfg, json_data=data, field_name="degree_type")
        if not degree_type:
            degree_type = self._infer_degree_type(name)
        
        # Clean up degree type (e.g. "Undergraduate" -> "UG")
        if degree_type:
            dt_lower = degree_type.lower()
            if "undergrad" in dt_lower: degree_type = "UG"
            elif "postgrad" in dt_lower: degree_type = "PG"
            elif "research" in dt_lower: degree_type = "PG"

        # 3. ATAR/Campuses
        campuses = []
        loc_cfg = config.extraction_map.get("location", {})
        location_raw = self._extract_field(None, loc_cfg, json_data=data, field_name="location")
        
        if location_raw:
            raw_list = re.split(r",|;| and ", str(location_raw), flags=re.IGNORECASE)
            from models import CampusLink
            for loc in raw_list:
                loc = loc.strip()
                campus_id = None
                if self._campus_name_map:
                    campus_id = self._campus_name_map.get(loc.lower())
                
                atar_cfg = config.extraction_map.get("atar", {})
                atar_rank = None
                
                rank_path = atar_cfg.get("json_path_template_rank")
                if rank_path:
                    path = rank_path.replace("{location}", loc.lower().replace(" ", ""))
                    raw_atar = self._extract_field(None, {"json_path": path}, json_data=data)
                    atar_rank = self._parse_atar(str(raw_atar))[1] if raw_atar else None

                campuses.append(CampusLink(
                    campus_id=campus_id or loc,
                    atar_lowest_selection_rank=atar_rank
                ))

        return CourseData(
            university_id=config.university_id,
            name=name,
            source_url=url,
            campuses=campuses,
            degree_type=degree_type,
            duration_years=duration,
            confidence_score=100
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
                json_path = field_cfg.get("json_path")
                if json_path and isinstance(data, dict):
                    if json_path == "latest_key":
                        keys = sorted(data.keys(), reverse=True)
                        if keys:
                            data = data[keys[0]]
                    else:
                        for k in json_path.split("."):
                            data = data.get(k, {})
                return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"Generic JSON extraction failure: {e}")
        return {}

    def find_by_anchor(self, soup: BeautifulSoup, anchor_text: str) -> str | None:
        """Locate data based on a nearby text label (e.g., \"ATAR\")."""
        labels = soup.find_all(string=lambda s: s and anchor_text.lower() in s.lower())

        for label_node in labels:
            full_text = label_node.strip()
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
        
        clean_html = self._preprocess_html(html, config)
        soup = BeautifulSoup(clean_html, "lxml")
        
        if self._should_discard_by_meta(soup, config):
            logger.info(f"Discarding hub/category page by meta tag: {url}")
            return None

        field_results = {}

        def unescape_text(val: str) -> str:
            if not val:
                return val
            if "\\" in val:
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
                if "\\u" in val:
                    try:
                        import codecs
                        val = codecs.decode(val, 'unicode_escape')
                    except:
                        pass
            return val.strip().strip('"').strip("'").strip()

        # 1. Extract Name
        name_cfg = config.extraction_map.get("name", {})
        name = self._extract_field(soup, name_cfg, html, field_name="name")
        
        if not name or name == "Unknown" or len(name) < 3:
            for key in ["awardTitle", "advertisedTitle", "award_title"]:
                m = re.search(f'"{key}"\\s*:\\s*"?([^",}}]+)"?', html)
                if m:
                    name = m.group(1).strip()
                    break
        
        if not name or name == "Unknown" or len(name) < 3:
            h1 = soup.select_one("h1")
            if h1:
                name = h1.get_text(strip=True)
        
        if not name or name == "Unknown" or len(name) < 3:
            name = url.split("/")[-1].replace("-", " ").title()

        name = unescape_text(name)
            
        if not name or not self._is_valid_course(name, url):
            return None

        filter_level = os.getenv("COURSE_LEVEL_FILTER", "UG")
        if filter_level == "UG":
            pg_keywords = ["master", "doctor", "graduate diploma", "graduate certificate", "postgraduate", "juris doctor"]
            if any(kw in name.lower() for kw in pg_keywords):
                logger.info(f"Skipping PG course by name: {name}")
                return None

        if name:
            field_results["name"] = name

        # 2. Extract Duration
        dur_cfg = config.extraction_map.get("duration", {})
        duration_str = self._extract_field(soup, dur_cfg, html, field_name="duration")
        
        if not duration_str:
            m = re.search(r'"duration"\s*:\s*"?([^",}]+)"?', html)
            if m:
                duration_str = m.group(1)

        duration = self._parse_duration(duration_str)
        
        if not duration:
            m = re.search(r'"totalCreditPoints"\s*:\s*(\d+)', html)
            if m:
                cp = int(m.group(1))
                if cp > 0:
                    duration = cp / 120.0
                    logger.debug(f"Inferred duration {duration} from {cp} credit points")

        if duration:
            field_results["duration"] = str(duration)

        deg_cfg = config.extraction_map.get("degree_type", {})
        degree_type = self._extract_field(soup, deg_cfg, html, field_name="degree_type")
        if not degree_type:
            degree_type = self._infer_degree_type(name)
            
        if filter_level == "UG" and degree_type in ["PG", "POSTGRAD", "POSTGRADUATE"]:
             logger.info(f"Skipping PG course by degree_type: {name} ({degree_type})")
             return None

        # 3. Extract ATAR
        atar_cfg = config.extraction_map.get("atar", {})
        atar_str = self._extract_field(soup, atar_cfg, clean_html, field_name="atar")
        atar_guaranteed, atar_rank = self._parse_atar(atar_str)

        atar_json_map = self._extract_json_map(clean_html, atar_cfg)

        if not duration and '"totalCreditPoints":0' in html.replace(" ", ""):
            logger.warning(f"Discarding potential non-course page: {url}")
            return None
        
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
                for k in ["commonwealth", "csp", "supported", "$", "a$"]
            )
            if not csp_available and any(k in clean_html.lower() for k in ["feedomesticcsp", "commonwealth supported"]):
                csp_available = True

        adm_cfg = config.extraction_map.get("admissions_codes", {})
        adm_codes = self.extract_admissions_codes(soup, adm_cfg)

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

                this_atar_guaranteed = atar_guaranteed
                this_atar_rank = atar_rank
                
                if atar_json_map and code_map:
                    codes_for_this_campus = [c.upper() for c, cid in code_map.items() if cid == campus_id]
                    for c in codes_for_this_campus:
                        if c in atar_json_map:
                            val = atar_json_map[c].get("minSelectionRankOffered")
                            if val and val not in ["N/A", "N/P", "NP", "RC"]:
                                try:
                                    this_atar_rank = float(val)
                                except:
                                    pass
                            
                            g_val = atar_json_map[c].get("aspireMinimumATAR")
                            if g_val and g_val not in ["N/A", "N/P", "NP", "RC"]:
                                try:
                                    this_atar_guaranteed = float(g_val)
                                except:
                                    pass
                            break

                campuses.append(
                    CampusLink(
                        campus_id=campus_id,
                        atar_guaranteed=this_atar_guaranteed,
                        atar_lowest_selection_rank=this_atar_rank,
                        admissions_codes=list(adm_codes), 
                        confidence_score=70,
                    )
                )

        # 7. Follow URLs
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
                        sub_adm_codes = self.extract_admissions_codes(
                            BeautifulSoup(sub_content, "lxml"), adm_cfg
                        )
                        sub_duration = None
                        m_sub_dur = re.search(r'"duration"\s*:\s*"?([^",}]+)"?', sub_content)
                        if m_sub_dur:
                            sub_duration = self._parse_duration(m_sub_dur.group(1))
                        
                        m_sub_cp = re.search(r'"totalCreditPoints"\s*:\s*(\d+)', sub_content)
                        if m_sub_cp:
                            cp = int(m_sub_cp.group(1))
                            if cp > 0:
                                inferred = cp / 120.0
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

        if not name or name == "Unknown" or len(name) < 3:
            logger.warning(f"Discarding result with invalid name '{name}' from {url}")
            return None

        if not atar_guaranteed and not atar_rank:
            try:
                if hasattr(self, "_run_id") and self._run_id:
                    await log_atar_issue(
                        self.pool, config.university_id, self._run_id, name, url, "missing_atar", "No ATAR found"
                    )
            except Exception as e:
                logger.error(f"Failed to record ATAR issue: {e}")

        faculty = self._infer_faculty(name)

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
        soup: BeautifulSoup | None,
        field_cfg: dict,
        full_text: str | None = None,
        field_name: str | None = None,
        json_data: dict | None = None
    ) -> str | None:
        val = None

        if json_data and "json_path" in field_cfg:
            path = field_cfg["json_path"]
            curr = json_data
            for part in path.split("."):
                if isinstance(curr, dict):
                    curr = curr.get(part)
                elif isinstance(curr, list) and part.isdigit():
                    curr = curr[int(part)]
                else:
                    curr = None
                    break
            if curr is not None:
                val = str(curr)

        if val:
            return val

        if not soup:
            return None

        json_ld_path = field_cfg.get("json_ld")
        if json_ld_path:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    parts = json_ld_path.split(".")
                    curr = data
                    for p in parts:
                        if isinstance(curr, dict):
                            if p in curr: curr = curr[p]
                            elif curr.get("@type") == p: continue
                            else: curr = None; break
                        elif isinstance(curr, list) and p.isdigit():
                            curr = curr[int(p)]
                        else:
                            curr = None; break
                    if curr and isinstance(curr, str):
                        val = curr; break
                except: continue

        if not val:
            anchor = field_cfg.get("anchor")
            if anchor: val = self.find_by_anchor(soup, anchor)

        if not val:
            selector = field_cfg.get("selector")
            if selector:
                key_text = field_cfg.get("key")
                if key_text:
                    rows = soup.select(selector)
                    for row in rows:
                        cells = row.find_all(["th", "td"])
                        if len(cells) >= 2 and key_text.lower() in cells[0].get_text(strip=True).lower():
                            val = cells[1].get_text(" ", strip=True); break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        attr = field_cfg.get("attr")
                        val = elem.get(attr) if attr else elem.get_text(strip=True)
                
        regex = field_cfg.get("regex")
        if regex:
            target_text = val if val else full_text
            if target_text:
                m = re.search(regex, target_text, re.IGNORECASE)
                if m:
                    try: val = m.group(1)
                    except IndexError: val = m.group(0)

        if val and isinstance(val, str):
            if "\\" in val:
                escapes = {"\\/": "/", "\\\"": "\"", "\\\\": "\\", "\\b": "\b", "\\f": "\f", "\\n": "\n", "\\r": "\r", "\\t": "\t"}
                for esc, sub in escapes.items():
                    if esc in val: val = val.replace(esc, sub)
                if "\\u" in val:
                    try:
                        import codecs
                        val = codecs.decode(val, 'unicode_escape')
                    except: pass
            val = val.strip().strip('"').strip("'").strip()
        return val

    def _parse_duration(self, text: str | None) -> float | None:
        if not text: return None
        m = re.search(r"(\d+(?:\.\d+)?)\s*(year|yr|month|mon|week|wk)", text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            if "month" in unit or "mon" in unit: val = val / 12.0
            elif "week" in unit or "wk" in unit: val = val / 52.0
            if 0.2 <= val <= 10.0: return val
        m_plain = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", text)
        if m_plain:
            val = float(m_plain.group(1))
            if 0.5 <= val <= 8.0: return val
        return None

    def _parse_atar(self, text: str | None) -> tuple[float | None, float | None]:
        if not text: return None, None
        matches = list(re.finditer(r"(\d{2}(?:\.\d+)?)", text))
        if not matches: return None, None
        guaranteed = None
        rank = None
        for m in matches:
            val = round(float(m.group(1)), 2)
            if not (50 <= val <= 99.95): continue
            start = max(0, m.start() - 30)
            context = text[start:m.start()].lower()
            is_g = any(k in context for k in ["guarantee", "aspire", "minimum"])
            is_r = any(k in context for k in ["rank", "lowest", "offered"])
            if is_g and is_r:
                if context.rfind("guarantee") > context.rfind("rank") or context.rfind("aspire") > context.rfind("rank"):
                    if guaranteed is None: guaranteed = val
                    elif rank is None: rank = val
                else:
                    if rank is None: rank = val
                    elif guaranteed is None: guaranteed = val
            elif is_g:
                if guaranteed is None: guaranteed = val
                elif rank is None: rank = val
            elif is_r or "atar" in context:
                if rank is None: rank = val
                elif guaranteed is None: guaranteed = val
            else:
                if rank is None: rank = val
                elif guaranteed is None: guaranteed = val
        return guaranteed, rank

    def extract_admissions_codes(self, soup: BeautifulSoup, config: dict) -> list[str]:
        results = set()
        selector = config.get("selector")
        anchor = config.get("anchor")
        regex = config.get("regex")
        if selector:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(" ", strip=True)
                if regex: results.update(re.findall(regex, text))
                else: results.add(text)
        if not results and anchor:
            label_text = self.find_by_anchor(soup, anchor)
            if label_text and regex: results.update(re.findall(regex, label_text))
        if not results and regex:
            results.update(re.findall(regex, soup.get_text(" ")))
        return sorted(list(results))

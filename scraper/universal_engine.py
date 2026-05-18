import asyncio
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


def _unescape_text(val: str) -> str:
    if not val:
        return val
    if "\\" in val:
        escapes = {"\\/": "/", "\\\"": "\"", "\\\\": "\\", "\\b": "\b", "\\f": "\f", "\\n": "\n", "\\r": "\r", "\\t": "\t"}
        for esc, sub in escapes.items():
            if esc in val:
                val = val.replace(esc, sub)
        if "\\u" in val:
            try:
                import codecs
                val = codecs.decode(val, 'unicode_escape')
            except:
                pass
    return " ".join(val.strip().strip('"').strip("'").split())


class UniversalEngine(BaseScraper):
    """
    Centralized scraping engine driven by database-stored configurations.
    Includes visual anchor fallback logic and confidence scoring.
    Supports Hybrid JSON/HTML scraping for rich sitemaps.
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
        discard_cfg = config.extraction_map.get("discard_meta")
        if not discard_cfg: return False
        if not isinstance(discard_cfg, list): discard_cfg = [discard_cfg]
        for rule in discard_cfg:
            name, content = rule.get("name"), rule.get("content")
            meta = soup.find("meta", {"name": name})
            if meta:
                meta_content = meta.get("content")
                if content is None or meta_content == content: return True
        return False

    def _is_valid_course(self, name: str, url: str) -> bool:
        if not name or name.lower() == "unknown" or len(name) <= 3: return False
        name_lower = name.lower()
        campuses = ["prahran", "hawthorn", "croydon", "wantirna", "bundoora", "bendigo", "melbourne city", "albury-wodonga", "mildura", "shepparton"]
        if name_lower in campuses: return False
        filter_level = os.getenv("COURSE_LEVEL_FILTER", "UG")
        if filter_level == "UG":
            if any(k in name_lower for k in ["master", "doctor", "juris doctor", "graduate certificate", "graduate diploma", "postgraduate"]):
                return False
        if "bachelor" in name_lower: return True
        return False

    async def _fetch_with_browser(self, url: str) -> str | None:
        """Fetch a URL using the browser context (Playwright)."""
        from browser import browser_context
        async with browser_context() as ctx:
            try:
                page = await ctx.new_page()
                # For JSON sources, we navigate to the base site first to get session cookies
                if self._config.extraction_map.get("source_type") == "json" and "search-json" in url:
                    await page.goto(self._config.base_url, wait_until="networkidle")
                    await asyncio.sleep(2)
                    # Attempt fetch from within the session
                    content = await page.evaluate(f"fetch('{url}').then(r => r.text())")
                else:
                    await page.goto(url, wait_until="networkidle")
                    content = await page.content()
                
                # Cleanup: Browser sometimes wraps JSON in tags
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    content = content[start:end]
                return content
            except Exception as e:
                logger.error(f"Browser fetch failed for {url}: {e}")
                return None

    async def discover_urls(self, rp: urllib.robotparser.RobotFileParser) -> list[str]:
        await self._ensure_config()
        disc_cfg = self._config.extraction_map.get("discovery_config", {})
        method = disc_cfg.get("method")
        fetch_mode = self._config.extraction_map.get("fetch_mode", "static")
        urls = []

        if method == "sitemap":
            sitemap_url = disc_cfg.get("url")
            include_patterns = disc_cfg.get("include_patterns", [])
            async def fetch_sitemap(url):
                if fetch_mode == "browser": return await self._fetch_with_browser(url), "text/xml"
                try:
                    async with make_client() as client:
                        resp = await client.get(url); resp.raise_for_status()
                        return resp.text, resp.headers.get("Content-Type", "")
                except: return await self._fetch_with_browser(url), "text/xml"
            content, _ = await fetch_sitemap(sitemap_url)
            if content:
                found = re.findall(r"<loc>(https?://[^<]+)</loc>", content)
                for url in found:
                    if not include_patterns or any(p in url for p in include_patterns): urls.append(url)

        elif method == "listing":
            listing_url = disc_cfg.get("url")
            if not listing_url: return []
            async def fetch_listing(url):
                if url.startswith("file://"):
                    path = url.replace("file://", "")
                    if not os.path.isabs(path): path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
                    if os.path.exists(path):
                        with open(path, 'r') as f: return f.read(), "application/json"
                    return None, None
                if fetch_mode == "browser": return await self._fetch_with_browser(url), "application/json"
                try:
                    async with make_client() as client:
                        resp = await client.get(url)
                        if resp.status_code == 403: raise PermissionError("403 Forbidden")
                        resp.raise_for_status()
                        return resp.text, resp.headers.get("Content-Type", "")
                except Exception as e:
                    logger.warning(f"Standard fetch failed for listing {url}, trying browser: {e}")
                    return await self._fetch_with_browser(url), "application/json"
            
            content, content_type = await fetch_listing(listing_url)
            if content:
                if "application/json" in content_type or listing_url.endswith("json") or "search-json" in listing_url or content.strip().startswith("{"):
                    try: data = json.loads(content)
                    except:
                        try: data = json.loads(re.search(r'(\{.*\})', content, re.DOTALL).group(1))
                        except: data = {}
                    results = data.get("response", {}).get("resultPacket", {}).get("results", [])
                    if results:
                        for r in results:
                            u = r.get("liveUrl") or r.get("url")
                            if u:
                                if not u.startswith("http"): u = "https:" + u if u.startswith("//") else self._config.base_url.rstrip("/") + u
                                if "/course/" in u.lower() or "bachelor" in r.get("title", "").lower():
                                    urls.append(u)
                                    if self.use_cache: self.snapshots.save(self.university_id, u, json.dumps(r), ext="json")
                else:
                    soup = BeautifulSoup(content, "lxml")
                    link_selector = disc_cfg.get("link_selector")
                    if link_selector:
                        links = soup.select(link_selector)
                        for a in links:
                            u = a.get("href")
                            if u:
                                if not u.startswith("http"): u = "https:" + u if u.startswith("//") else self._config.base_url.rstrip("/") + u
                                urls.append(u)
                    if not urls and "resultPacket" not in content:
                        found = re.findall(r'"(https?://[^"]+)"', content)
                        for u in found:
                            if not any(ext in u.lower() for ext in [".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".pdf", ".woff"]): urls.append(u)
        return list(set(urls))

    async def scrape_url(self, rp: urllib.robotparser.RobotFileParser, url: str) -> CourseData | None:
        await self._ensure_config()
        self.check_robots(rp, url)
        
        foundational_data = None
        if self.use_cache:
            cached_json = self.snapshots.load(self.university_id, url, ext="json")
            if cached_json:
                try: foundational_data = json.loads(cached_json)
                except: pass

        html_content = None
        if self.use_cache:
            html_content = self.snapshots.load(self.university_id, url, ext="html", force_refresh=self.force_refresh)
        
        if not html_content:
            fetch_mode = self._config.extraction_map.get("fetch_mode", "static")
            if fetch_mode == "browser":
                html_content = await self._fetch_with_browser(url)
            else:
                try:
                    async with make_client() as client:
                        resp = await client.get(url)
                        if resp.status_code == 403: raise PermissionError("403 Forbidden")
                        resp.raise_for_status()
                        html_content = resp.text
                except Exception as e:
                    logger.warning(f"Standard fetch failed for {url}, trying browser: {e}")
                    html_content = await self._fetch_with_browser(url)
            if html_content and self.use_cache: self.snapshots.save(self.university_id, url, html_content, ext="html")

        if not html_content and not foundational_data: return None

        async def fetch_sub(sub_url: str) -> str:
            ext = "json" if "json" in sub_url or "/data/" in sub_url else "html"
            if self.use_cache:
                cached = self.snapshots.load(self.university_id, sub_url, ext=ext)
                if cached: return cached
            async with make_client() as client:
                resp = await client.get(sub_url); resp.raise_for_status()
                if self.use_cache: self.snapshots.save(self.university_id, sub_url, resp.text, ext=ext)
                return resp.text

        return await self.scrape_page(html_content or "", self._config, url, campus_map=self._campus_name_map, code_map=self._campus_code_map, fetch_fn=fetch_sub, json_data=foundational_data)

    async def scrape_page(self, html: str, config: SiteConfig, url: str, campus_map: dict[str, str] | None = None, code_map: dict[str, str] | None = None, fetch_fn: Any | None = None, json_data: dict | None = None) -> CourseData | None:
        clean_html = self._preprocess_html(html, config)
        soup = BeautifulSoup(clean_html, "lxml")
        if self._should_discard_by_meta(soup, config): return None

        # 1. Name
        name_cfg = config.extraction_map.get("name", {})
        name = self._extract_field(soup, name_cfg, html, field_name="name", json_data=json_data)
        if not name or name == "Unknown" or len(name) < 3:
            for key in ["awardTitle", "advertisedTitle", "award_title"]:
                m = re.search(f'"{key}"\\s*:\\s*"?([^",}}]+)"?', html)
                if m: name = m.group(1).strip(); break
        if (not name or name == "Unknown" or len(name) < 3) and soup:
            h1 = soup.select_one("h1")
            if h1: name = h1.get_text(strip=True)
        if (not name or name == "Unknown" or len(name) < 3) and json_data: name = json_data.get("title")
        name = _unescape_text(name or "")
        if not name or not self._is_valid_course(name, url): return None

        # 2. Duration
        dur_cfg = config.extraction_map.get("duration", {})
        duration_str = self._extract_field(soup, dur_cfg, html, field_name="duration", json_data=json_data)
        duration = self._parse_duration(duration_str)
        if not duration and html:
            m = re.search(r'"duration"\s*:\s*"?([^",}]+)"?', html)
            if m: duration = self._parse_duration(m.group(1))

        # 3. Degree Type
        deg_cfg = config.extraction_map.get("degree_type", {})
        degree_type = self._extract_field(soup, deg_cfg, html, field_name="degree_type", json_data=json_data)
        if not degree_type: degree_type = self._infer_degree_type(name)
        if degree_type:
            dt_lower = degree_type.lower()
            if "undergrad" in dt_lower: degree_type = "UG"
            elif "postgrad" in dt_lower: degree_type = "PG"

        # 4. ATAR
        atar_cfg = config.extraction_map.get("atar", {})
        atar_str = self._extract_field(soup, atar_cfg, clean_html, field_name="atar", json_data=json_data)
        atar_guaranteed, atar_rank = self._parse_atar(atar_str)

        # 5. Fees / CSP
        fees_cfg = config.extraction_map.get("fees", {})
        fees_str = self._extract_field(soup, fees_cfg, clean_html, field_name="fees")
        csp_available = False
        if fees_str:
            csp_available = any(k in fees_str.lower() for k in ["commonwealth", "csp", "supported", "$", "a$"])
        if not csp_available and any(k in clean_html.lower() for k in ["feedomesticcsp", "commonwealth supported"]):
            csp_available = True

        # 6. Admissions codes
        adm_cfg = config.extraction_map.get("admissions_codes", {})
        adm_codes = self.extract_admissions_codes(soup, adm_cfg, full_html=clean_html)

        # 7. Campuses — campus_array path OR standard location path
        array_cfg = config.extraction_map.get("campus_array")
        if array_cfg:
            campuses = self._extract_campus_array(clean_html, array_cfg)
            if not campuses:
                return None
            if adm_codes and not any(c.admissions_codes for c in campuses):
                for c in campuses:
                    c.admissions_codes = list(adm_codes)
        else:
            # 7. Location
            loc_cfg = config.extraction_map.get("location", {})
            location_raw = self._extract_field(soup, loc_cfg, clean_html, field_name="location", json_data=json_data)
            campuses = []
            if location_raw:
                location_str = str(location_raw).strip()
                location_str = re.sub(r'<br\s*/?>', ',', location_str, flags=re.IGNORECASE)
                location_str = re.sub(r'<[^>]+>', '', location_str)
                if location_str.startswith("[") and location_str.endswith("]"):
                    try:
                        raw_list = json.loads(location_str)
                    except Exception:
                        raw_list = re.split(r",|;| and ", location_str, flags=re.IGNORECASE)
                else:
                    raw_list = re.split(r",|;| and ", location_str, flags=re.IGNORECASE)
                raw_list = [re.sub(r'\s*\([^)]*\)', '', loc).strip() for loc in raw_list if loc.strip()]
                location_mapping = loc_cfg.get("mapping", {})
                from models import CampusLink
                for loc in raw_list:
                    loc = loc.strip()
                    campus_id = location_mapping.get(loc) if location_mapping else None
                    if not campus_id and self._campus_name_map:
                        campus_id = self._campus_name_map.get(loc.lower())
                    this_atar_rank = atar_rank
                    rank_path = atar_cfg.get("json_path_template_rank")
                    if rank_path and json_data:
                        path = rank_path.replace("{location}", loc.lower().replace(" ", ""))
                        raw_atar = self._extract_field(None, {"json_path": path}, json_data=json_data)
                        parsed_rank = self._parse_atar(str(raw_atar))[1] if raw_atar else None
                        if parsed_rank: this_atar_rank = parsed_rank
                    campuses.append(CampusLink(
                        campus_id=campus_id or loc,
                        atar_lowest_selection_rank=this_atar_rank,
                        atar_guaranteed=atar_guaranteed,
                        admissions_codes=list(adm_codes),
                    ))
                seen_ids: set = set()
                campuses = [c for c in campuses if not (c.campus_id in seen_ids or seen_ids.add(c.campus_id))]

            # 7b. Per-campus ATAR override from allAtars-style JSON map
            if atar_cfg.get("json_regex") and campuses and code_map:
                atar_map = self._extract_json_map(clean_html, atar_cfg)
                if atar_map:
                    inv_code_map = {v: k for k, v in code_map.items()}
                    for c in campuses:
                        campus_code = inv_code_map.get(c.campus_id, "")
                        campus_data = atar_map.get(campus_code.upper()) or atar_map.get(campus_code)
                        if campus_data:
                            rank_val = campus_data.get("minSelectionRankOffered")
                            guaranteed_val = campus_data.get("aspireMinimumATAR")
                            if rank_val:
                                try:
                                    c.atar_lowest_selection_rank = round(float(rank_val), 2)
                                except (ValueError, TypeError):
                                    pass
                            if guaranteed_val:
                                try:
                                    c.atar_guaranteed = round(float(guaranteed_val), 2)
                                except (ValueError, TypeError):
                                    pass

        # Log missing ATAR if config requests it (e.g. VU where many courses have no ATAR)
        atar_issues: list[tuple[str, str]] = []
        if atar_cfg.get("log_missing") and campuses and not any(
            c.atar_lowest_selection_rank or c.atar_guaranteed for c in campuses
        ):
            atar_issues.append(("no_atar", "No ATAR found — course may not require one"))

        # 8. Follow URLs (e.g. La Trobe data API sub-pages for admissions codes)
        follow_cfg = config.extraction_map.get("follow_urls")
        if follow_cfg and fetch_fn:
            regex = follow_cfg.get("regex")
            delay = follow_cfg.get("delay", 0.5)
            if regex:
                matches = re.findall(regex, clean_html)
                for sub_url in matches:
                    if not sub_url.startswith("http"):
                        sub_url = config.base_url.rstrip("/") + "/" + sub_url.lstrip("/")
                    try:
                        await asyncio.sleep(delay)
                        sub_content = await fetch_fn(sub_url)
                        if not sub_content:
                            continue
                        sub_soup = BeautifulSoup(sub_content, "lxml")
                        sub_adm_codes = self.extract_admissions_codes(sub_soup, adm_cfg, full_html=sub_content)
                        sub_duration = self._parse_duration(
                            next((m.group(1) for m in [re.search(r'"duration"\s*:\s*"?([^",}]+)"?', sub_content)] if m), None)
                        )
                        if sub_adm_codes or sub_duration:
                            matched = next(
                                (c for c in campuses if code_map and
                                 any(f"/{k}/" in sub_url.lower() for k, v in code_map.items() if v == c.campus_id)),
                                None
                            )
                            targets = [matched] if matched else campuses
                            for c in targets:
                                if sub_adm_codes:
                                    c.admissions_codes = sorted(set(c.admissions_codes) | set(sub_adm_codes))
                                if sub_duration:
                                    duration = sub_duration
                    except Exception as e:
                        logger.error(f"Failed to fetch follow URL {sub_url}: {e}")

        return CourseData(
            university_id=config.university_id,
            name=name,
            source_url=url,
            faculty=self._infer_faculty(name),
            campuses=campuses,
            degree_type=degree_type,
            duration_years=duration,
            csp_available=csp_available if csp_available else None,
            confidence_score=90 if json_data else 70,
            atar_issues=atar_issues,
        )

    def _extract_field(self, soup: BeautifulSoup | None, field_cfg: dict, full_text: str | None = None, field_name: str | None = None, json_data: dict | None = None) -> str | None:
        val = None
        if json_data and "json_path" in field_cfg:
            path, curr = field_cfg["json_path"], json_data
            for part in path.split("."):
                if isinstance(curr, dict): curr = curr.get(part)
                elif isinstance(curr, list) and part.isdigit(): curr = curr[int(part)]
                else: curr = None; break
            if curr is not None: val = str(curr)
        if val: return val
        if not soup: return None
        json_ld_path = field_cfg.get("json_ld")
        if json_ld_path:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data, parts = json.loads(script.string), json_ld_path.split(".")
                    curr = data
                    for p in parts:
                        if isinstance(curr, dict):
                            if p in curr: curr = curr[p]
                            elif curr.get("@type") == p: continue
                            else: curr = None; break
                        elif isinstance(curr, list) and p.isdigit(): curr = curr[int(p)]
                        else: curr = None; break
                    if curr and isinstance(curr, str): val = curr; break
                except: continue
        if not val and field_cfg.get("anchor"): val = self.find_by_anchor(soup, field_cfg["anchor"])
        if not val and field_cfg.get("selector"):
            key_text = field_cfg.get("key")
            if key_text:
                for row in soup.select(field_cfg["selector"]):
                    cells = row.find_all(["th", "td"])
                    if len(cells) >= 2 and key_text.lower() in cells[0].get_text(strip=True).lower(): val = cells[1].get_text(" ", strip=True); break
            else:
                elem = soup.select_one(field_cfg["selector"])
                if elem: val = elem.get(field_cfg.get("attr")) if field_cfg.get("attr") else elem.get_text(strip=True)
        if field_cfg.get("regex"):
            target = val if val else (full_text or soup.get_text())
            if target:
                m = re.search(field_cfg["regex"], target, re.IGNORECASE)
                if m:
                    try: val = m.group(1)
                    except IndexError: val = m.group(0)
        return _unescape_text(val) if val else None

    def _parse_duration(self, text: str | None) -> float | None:
        if not text: return None
        m = re.search(r"(\d+(?:\.\d+)?)\s*(year|yr|month|mon|week|wk)", text, re.IGNORECASE)
        if m:
            val, unit = float(m.group(1)), m.group(2).lower()
            if "month" in unit or "mon" in unit: val /= 12.0
            elif "week" in unit or "wk" in unit: val /= 52.0
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
        guaranteed, rank = None, None
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

    def find_by_anchor(self, soup: BeautifulSoup, anchor_text: str) -> str | None:
        for label_node in soup.find_all(string=lambda s: s and anchor_text.lower() in s.lower()):
            full_text = label_node.strip()
            if any(c.isdigit() for c in full_text) or any(k in full_text.lower() for k in ["available", "yes", "no"]) or (":" in full_text and len(full_text.split(":", 1)[1].strip()) > 0): return full_text
            curr = label_node.parent if hasattr(label_node, "parent") else label_node
            while curr:
                next_text = curr.find_next(string=True)
                if not next_text: break
                text = next_text.strip()
                if text and anchor_text.lower() not in text.lower(): return text
                curr = next_text
        return None

    def extract_admissions_codes(self, soup: BeautifulSoup, config: dict, full_html: str | None = None) -> list[str]:
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
            results.update(re.findall(regex, full_html or soup.get_text(" ")))
        return sorted(list(results))

    def _extract_json_map(self, text: str, field_cfg: dict) -> dict | None:
        json_regex = field_cfg.get("json_regex")
        json_path = field_cfg.get("json_path")
        if not json_regex:
            return None
        m = re.search(json_regex, text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(1))
        except Exception:
            return None
        if json_path == "latest_key" and isinstance(data, dict):
            sorted_keys = sorted(data.keys(), reverse=True)
            if sorted_keys:
                return data[sorted_keys[0]]
        return data

    def _extract_campus_array(self, html: str, cfg: dict) -> list["CampusLink"]:
        from models import CampusLink

        array_regex = cfg.get("array_regex")
        if not array_regex:
            return []

        m = re.search(array_regex, html, re.DOTALL)
        if not m:
            logger.debug("campus_array: regex did not match any script content")
            return []

        try:
            raw_array = json.loads(m.group(1))
        except (json.JSONDecodeError, IndexError) as exc:
            logger.warning(f"campus_array: JSON parse error — {exc}")
            return []

        if not isinstance(raw_array, list):
            logger.warning("campus_array: parsed value is not a list")
            return []

        campus_title_key = cfg.get("campus_title_key", "CampusTitle")
        atar_key         = cfg.get("atar_key", "ATARCode")
        atar_regex       = cfg.get("atar_regex", r"(\d{2,3}(?:\.\d+)?)")
        tac_code_key     = cfg.get("tac_code_key", "TACCode")
        tac_label_key    = cfg.get("tac_label_key", "Code")
        vtac_filter      = cfg.get("vtac_filter", "VTAC code")
        mapping: dict[str, str] = cfg.get("mapping", {})

        seen_ids: set[str] = set()
        links: list[CampusLink] = []

        for item in raw_array:
            if not isinstance(item, dict):
                continue

            campus_title = item.get(campus_title_key, "")
            campus_id = mapping.get(campus_title)
            if not campus_id or campus_id in seen_ids:
                continue
            seen_ids.add(campus_id)

            atar_val: float | None = None
            atar_raw = item.get(atar_key, "")
            if atar_raw:
                am = re.search(atar_regex, str(atar_raw))
                if am:
                    try:
                        candidate = round(float(am.group(1)), 2)
                        if 50 <= candidate <= 99.95:
                            atar_val = candidate
                    except (ValueError, TypeError):
                        pass

            admissions_codes: list[str] = []
            raw_code = item.get(tac_code_key, "")
            raw_label = item.get(tac_label_key, "")
            if raw_label == vtac_filter and raw_code:
                clean_code = re.sub(r"<[^>]+>", "", str(raw_code)).strip()
                if clean_code:
                    admissions_codes.append(clean_code)

            links.append(CampusLink(
                campus_id=campus_id,
                atar_lowest_selection_rank=atar_val,
                atar_guaranteed=None,
                admissions_codes=admissions_codes,
            ))

        if not links:
            logger.warning("campus_array: no recognized campuses found — check mapping config")
        return links

    def _preprocess_html(self, html: str, config: SiteConfig) -> str:
        cleanup = config.extraction_map.get("cleanup_regexes", [])
        for regex in cleanup:
            try: html = re.sub(regex, '', html, flags=re.DOTALL)
            except: pass
        return html

    async def get_config(self, university_id: str) -> SiteConfig:
        config = await get_site_config(self.pool, university_id)
        if not config: raise ValueError(f"No active SiteConfig found for university_id: {university_id}")
        return config

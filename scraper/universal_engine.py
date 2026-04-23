import logging
import re
import json
from typing import Any

from bs4 import BeautifulSoup
from psycopg_pool import AsyncConnectionPool

from db import get_site_config
from models import SiteConfig, CourseData

logger = logging.getLogger(__name__)

class UniversalEngine:
    """
    Centralized scraping engine driven by database-stored configurations.
    Includes visual anchor fallback logic and confidence scoring.
    """

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def get_config(self, university_id: str) -> SiteConfig:
        """Fetch the active configuration for the given university."""
        config = await get_site_config(self.pool, university_id)
        if not config:
            raise ValueError(f"No active SiteConfig found for university_id: {university_id}")
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
            # It's a value if it contains numbers and is significantly longer than the anchor
            if any(c.isdigit() for c in full_text) and len(full_text) > len(anchor_text) + 2:
                logger.debug(f"Found value in same node as anchor '{anchor_text}': {full_text}")
                return full_text

            # 2. Otherwise, look for the next non-empty string that isn't the label itself
            if hasattr(label_node, 'parent'):
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
                    logger.debug(f"Found value in subsequent node for anchor '{anchor_text}': {text}")
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

    async def scrape_page(self, html: str, config: SiteConfig, url: str) -> CourseData:
        """Scrape a course page using the provided configuration."""
        soup = BeautifulSoup(html, "lxml")
        field_results = {}

        # 1. Extract Name
        name_cfg = config.extraction_map.get("name", {})
        name = self._extract_field(soup, name_cfg, html)
        if name:
            field_results["name"] = name

        # 2. Extract Duration
        dur_cfg = config.extraction_map.get("duration", {})
        # Note: UniMelb duration is sometimes found with "Duration" label
        duration_str = self._extract_field(soup, dur_cfg, html)
        if not duration_str:
            # Fallback specifically for UniMelb structure
            dur_label = soup.find(string=lambda s: s and "Duration" in s)
            if dur_label:
                # Get the parent, and look for text within it
                parent = dur_label.find_parent()
                if parent:
                    # Look for the duration in the parent or next sibling
                    text_content = parent.get_text(" ", strip=True)
                    logger.debug(f"Duration parent text: {text_content}")
                    duration_str = text_content
        
        duration = self._parse_duration(duration_str)
        if duration:
            field_results["duration"] = str(duration)

        # 3. Extract ATAR
        atar_cfg = config.extraction_map.get("atar", {})
        atar_str = self._extract_field(soup, atar_cfg, html)
        atar_guaranteed, atar_rank = self._parse_atar(atar_str)
        if atar_guaranteed or atar_rank:
            field_results["atar"] = atar_str

        # 4. Extract Fees
        fees_cfg = config.extraction_map.get("fees", {})
        # Check anchor specifically for CSP availability
        anchor = fees_cfg.get("anchor")
        csp_available = False
        if anchor:
            anchor_val = self.find_by_anchor(soup, anchor)
            if anchor_val:
                # Generous detection: commonwealth, csp, supported, or just a dollar sign for domestic fees
                csp_available = any(k in anchor_val.lower() for k in ["commonwealth", "csp", "supported", "$"])
                field_results["fees"] = anchor_val
        
        # Fallback to general extraction (including regex on whole HTML)
        if not csp_available:
            fees_str = self._extract_field(soup, fees_cfg, html)
            if fees_str:
                field_results["fees"] = fees_str
                # If regex found something and it looks like a price, or contains CSP keywords
                csp_available = any(k in fees_str.lower() for k in ["commonwealth", "csp", "supported", "$"])
                # Fallback: if regex matched "FeeDomesticCSP" (we check the regex string in config)
                if not csp_available and "FeeDomesticCSP" in fees_cfg.get("regex", ""):
                    csp_available = True

        # 5. Admissions Codes
        adm_cfg = config.extraction_map.get("admissions_codes", {})
        adm_codes = self.extract_admissions_codes(soup, adm_cfg)
        if adm_codes:
            field_results["admissions_codes"] = ",".join(adm_codes)

        # 6. Location / Campuses
        loc_cfg = config.extraction_map.get("location", {})
        location_str = self._extract_field(soup, loc_cfg, html)
        
        campuses = []
        if location_str:
            from models import CampusLink
            # Simple mapping for now
            campuses.append(CampusLink(
                campus_id=location_str, # Will be mapped to real ID in Phase 3
                atar_guaranteed=atar_guaranteed,
                atar_lowest_selection_rank=atar_rank,
                admissions_codes=adm_codes,
                confidence_score=70
            ))

        confidence = self.calculate_confidence(field_results)

        return CourseData(
            university_id=config.university_id,
            name=name or "Unknown",
            source_url=url,
            campuses=campuses,
            degree_type="UG",
            duration_years=duration,
            csp_available=csp_available,
            confidence_score=confidence
        )

    def _extract_field(self, soup: BeautifulSoup, field_cfg: dict, full_html: str | None = None) -> str | None:
        """Helper to extract a field based on selector, attr, anchor, or regex."""
        import json
        val = None
        
        # 1. Try JSON-LD first if specified
        json_ld_path = field_cfg.get("json_ld")
        if json_ld_path:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    content = script.string or script.text
                    if not content: continue
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
                    if val: break
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
                        if len(cells) >= 2 and key_text.lower() in cells[0].get_text(strip=True).lower():
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
            target_text = val if val else full_html
            if target_text:
                logger.debug(f"Applying regex '{regex}' to text length {len(target_text)}")
                m = re.search(regex, target_text, re.IGNORECASE)
                if m:
                    try:
                        val = m.group(1)
                    except IndexError:
                        val = m.group(0)
                    logger.debug(f"Regex match result: {val}")
                elif val:
                    # If regex was supposed to refine a value but failed, clear it
                    val = None
                    logger.debug("Regex did not match")
                
        return val

    def _parse_duration(self, text: str | None) -> float | None:
        if not text: return None
        m = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(m.group(1)) if m else None

    def _parse_atar(self, text: str | None) -> tuple[int | None, int | None]:
        """
        Return (atar_guaranteed, atar_lowest_selection_rank) from text.
        """
        if not text: return None, None
        
        guaranteed = None
        rank = None
        
        # Look for numbers, but filter out years (e.g. 2024, 2025, 2026)
        # ATARs are always <= 99.95
        m = re.findall(r"(\d{2,4}(?:\.\d+)?)", text)
        if not m: return None, None
        
        vals = []
        for n in m:
            val = float(n)
            # If it's a 4-digit integer starting with 20, it's likely a year
            if 1900 <= val <= 2100:
                continue
            vals.append(int(val))
            
        if not vals: return None, None
        
        lower_text = text.lower()
        if "guarantee" in lower_text:
            guaranteed = vals[0]
            if len(vals) > 1: rank = vals[1]
        elif "selection rank" in lower_text or "rank" in lower_text:
            rank = vals[0]
            if len(vals) > 1: guaranteed = vals[1]
        else:
            # Fallback if no keywords found
            guaranteed = vals[0]
            if len(vals) > 1: rank = vals[1]
            
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

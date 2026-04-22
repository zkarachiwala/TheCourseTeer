import logging
import re
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
        Searches for the label and returns the text of the next sibling or parent's sibling.
        """
        # Find the element containing the anchor text
        label_node = soup.find(string=re.compile(rf"\b{re.escape(anchor_text)}\b", re.IGNORECASE))
        if not label_node:
            return None
        
        # Try finding text in the next sibling or subsequent elements
        # We look for the first non-empty string that isn't the label itself
        curr = label_node
        while curr:
            next_text = curr.find_next(string=True)
            if not next_text:
                break
            text = next_text.strip()
            if text and text.lower() != anchor_text.lower():
                return text
            curr = next_text
                
        return None

    def extract_admissions_codes(self, soup: BeautifulSoup, config: dict) -> list[str]:
        """
        Extract admissions codes (VTAC, UAC, etc.) based on anchor or regex.
        Returns a list of unique codes found.
        """
        results = set()
        
        # Try finding by anchor label first
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
        
        # Fallback to general regex search on the whole page if no anchor result
        if not results and regex:
            text = soup.get_text(" ")
            matches = re.findall(regex, text)
            results.update(matches)
            
        return sorted(list(results))

    def calculate_confidence(self, field_results: dict[str, str]) -> int:
        """
        Calculate an overall confidence score for the scraped data.
        - 100: All fields matched via primary selectors.
        - 70: Some fields matched via anchors/regex.
        - 30: Default values or failures present.
        """
        # TODO: Implement granular per-field confidence tracking
        # For now, if we have a name and at least one other field, return 100
        if field_results.get("name") and len(field_results) > 2:
            return 100
        async def scrape_page(self, html: str, config: SiteConfig, url: str) -> CourseData:
            """Scrape a course page using the provided configuration."""
            soup = BeautifulSoup(html, "lxml")
            field_results = {}

            # 1. Extract Name
            name_cfg = config.extraction_map.get("name", {})
            name = self._extract_field(soup, name_cfg)
            if name:
                field_results["name"] = name

            # 2. Extract Duration
            dur_cfg = config.extraction_map.get("duration", {})
            duration_str = self._extract_field(soup, dur_cfg)
            duration = self._parse_duration(duration_str)
            if duration:
                field_results["duration"] = str(duration)

            # 3. Extract ATAR
            atar_cfg = config.extraction_map.get("atar", {})
            atar_str = self._extract_field(soup, atar_cfg)
            atar_guaranteed, atar_rank = self._parse_atar(atar_str)
            if atar_guaranteed or atar_rank:
                field_results["atar"] = atar_str

            # 4. Extract Fees
            fees_cfg = config.extraction_map.get("fees", {})
            fees_str = self._extract_field(soup, fees_cfg)
            csp_available = "commonwealth" in (fees_str or "").lower()
            if fees_str:
                field_results["fees"] = fees_str

            # 5. Admissions Codes
            adm_cfg = config.extraction_map.get("admissions_codes", {})
            adm_codes = self.extract_admissions_codes(soup, adm_cfg)
            if adm_codes:
                field_results["admissions_codes"] = ",".join(adm_codes)

            confidence = self.calculate_confidence(field_results)

            return CourseData(
                university_id=config.university_id,
                name=name or "Unknown",
                source_url=url,
                campuses=[], # To be implemented in Phase 3
                degree_type="UG",
                duration_years=duration,
                csp_available=csp_available,
                confidence_score=confidence
            )

        def _extract_field(self, soup: BeautifulSoup, field_cfg: dict) -> str | None:
            """Helper to extract a field based on selector, attr, anchor, or regex."""
            val = None

            # Try selector first
            selector = field_cfg.get("selector")
            if selector:
                elem = soup.select_one(selector)
                if elem:
                    attr = field_cfg.get("attr")
                    val = elem.get(attr) if attr else elem.get_text(strip=True)

            # Fallback to anchor
            if not val:
                anchor = field_cfg.get("anchor")
                if anchor:
                    val = self.find_by_anchor(soup, anchor)

            # Apply regex if provided
            regex = field_cfg.get("regex")
            if val and regex:
                m = re.search(regex, val, re.IGNORECASE)
                if m:
                    # Use group 1 if it exists, else full match
                    try:
                        val = m.group(1)
                    except IndexError:
                        val = m.group(0)

            return val

        def _parse_duration(self, text: str | None) -> float | None:
            if not text: return None
            m = re.search(r"(\d+(?:\.\d+)?)", text)
            return float(m.group(1)) if m else None

        def _parse_atar(self, text: str | None) -> tuple[int | None, int | None]:
            # Simplistic parser for now
            if not text: return None, None
            m = re.findall(r"(\d{2}(?:\.\d+)?)", text)
            nums = [int(float(n)) for n in m]
            if len(nums) >= 2: return nums[0], nums[1]
            if len(nums) == 1: return nums[0], None
            return None, None

        def extract_admissions_codes(self, soup: BeautifulSoup, config: dict) -> list[str]:


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
        return 70

    async def scrape_page(self, html: str, config: SiteConfig, url: str) -> CourseData:
        """Scrape a course page using the provided configuration."""
        soup = BeautifulSoup(html, "lxml")
        field_results = {}
        
        # 1. Extract Name
        name_cfg = config.extraction_map.get("name", {})
        name = None
        if "selector" in name_cfg:
            elem = soup.select_one(name_cfg["selector"])
            if elem:
                name = elem.get_text(strip=True)
                field_results["name"] = name
        if not name and "anchor" in name_cfg:
            name = self.find_by_anchor(soup, name_cfg["anchor"])
            if name:
                field_results["name"] = name
            
        # 2. Admissions Codes
        adm_cfg = config.extraction_map.get("admissions_codes", {})
        adm_codes = self.extract_admissions_codes(soup, adm_cfg)
        if adm_codes:
            field_results["admissions_codes"] = ",".join(adm_codes)
        
        confidence = self.calculate_confidence(field_results)
        
        # Placeholder for remaining fields (duration, fees, location)
        return CourseData(
            university_id=config.university_id,
            name=name or "Unknown",
            source_url=url,
            campuses=[], # Logic to be added in Phase 3
            confidence_score=confidence
        )

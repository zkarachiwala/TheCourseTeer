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

    async def scrape_page(self, html: str, config: SiteConfig) -> CourseData:
        """Scrape a course page using the provided configuration."""
        soup = BeautifulSoup(html, "lxml")
        # To be implemented in next tasks
        pass

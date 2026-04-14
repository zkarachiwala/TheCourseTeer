from bs4 import BeautifulSoup
from psycopg_pool import AsyncConnectionPool

from ai_remap import remap_selector
from db import upsert_selector


class SelectorError(Exception):
    pass


async def extract_field(
    pool: AsyncConnectionPool,
    university_id: str,
    field_name: str,
    html: str,
    selector: str,
    mode: str = "static",
) -> str | None:
    """
    Extract a single field from html using a CSS selector.

    On failure, calls the AI re-mapper to get a replacement selector,
    persists it to scraper_configs, and retries once. Returns None if
    both attempts fail.
    """
    try:
        return _apply_selector(html, selector)
    except Exception:
        pass

    new_selector = await remap_selector(field_name, selector, html)
    await upsert_selector(pool, university_id, field_name, new_selector, ai_generated=True, mode=mode)

    try:
        return _apply_selector(html, new_selector)
    except SelectorError:
        return None


def _apply_selector(html: str, selector: str) -> str:
    """Apply a CSS selector and return the text of the first match.

    Raises SelectorError if nothing is found.
    """
    soup = BeautifulSoup(html, "lxml")
    element = soup.select_one(selector)
    if element is None:
        raise SelectorError(f"Selector matched nothing: {selector!r}")
    return element.get_text(strip=True)

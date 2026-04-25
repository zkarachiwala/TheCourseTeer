import urllib.robotparser

import httpx
from psycopg_pool import AsyncConnectionPool

from db import store_robots_rules
from http_client import BROWSER_UA


async def fetch_and_store_robots(
    pool: AsyncConnectionPool,
    university_id: str,
    homepage_url: str,
    client: httpx.AsyncClient,
) -> urllib.robotparser.RobotFileParser:
    """
    Fetch robots.txt for homepage_url, parse it, persist rules to DB, and
    return the parser for immediate path checking.

    Uses the provided httpx client (with browser UA) so Cloudflare-protected
    sites are handled transparently.
    """
    robots_url = homepage_url.rstrip("/") + "/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        response = await client.get(robots_url)
        response.raise_for_status()
        content = response.text
        # Cloudflare challenge pages return HTML instead of robots.txt — treat as no rules.
        if content.lstrip().lower().startswith("<!doctype"):
            print(f"Warning: robots.txt fetch returned HTML (Cloudflare?) for {robots_url} — treating as no restrictions")
            content = ""
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            content = ""  # no robots.txt — no restrictions
        else:
            print(f"Warning: robots.txt fetch returned {e.response.status_code} for {robots_url} — treating as no restrictions")
            content = ""
    except httpx.HTTPError:
        content = ""

    rp.parse(content.splitlines())

    rules = _serialise_rules(rp)
    await store_robots_rules(pool, university_id, rules)

    return rp


def is_allowed(rp: urllib.robotparser.RobotFileParser, url: str) -> bool:
    """Return True if url is allowed to be fetched by our User-Agent."""
    return rp.can_fetch(BROWSER_UA, url)


def _serialise_rules(rp: urllib.robotparser.RobotFileParser) -> dict:
    """Extract allow/disallow/crawl-delay from the parser into a plain dict."""
    entries = {}
    for entry in rp.entries:
        agents = list(entry.useragents) or ["*"]
        rules = {
            "allow": [r.path for r in entry.rulelines if r.allowance],
            "disallow": [r.path for r in entry.rulelines if not r.allowance],
        }
        for agent in agents:
            entries[agent] = rules

    if rp.default_entry:
        rules = {
            "allow": [r.path for r in rp.default_entry.rulelines if r.allowance],
            "disallow": [r.path for r in rp.default_entry.rulelines if not r.allowance],
        }
        entries.setdefault("*", rules)

    return entries

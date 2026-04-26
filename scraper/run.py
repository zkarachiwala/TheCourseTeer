"""Entry point for the course scraper.

Usage:
  uv run python run.py                        # resume all scrapers
  uv run python run.py --university monash    # resume monash only
  uv run python run.py --force                # reset all and re-scrape
  uv run python run.py --force --university monash  # reset monash only
"""
import argparse
import asyncio
import sys

from dotenv import load_dotenv

from base_scraper import BaseScraper
from db import get_pool
from universal_engine import UniversalEngine

SCRAPERS: dict[str, type[BaseScraper]] = {
    "latrobe": UniversalEngine,
    "monash": UniversalEngine,
    "rmit": UniversalEngine,
    "swinburne": UniversalEngine,
    "unimelb": UniversalEngine,
}


async def main(universities: list[str], force: bool, use_cache: bool = True, refresh: bool = False) -> None:
    load_dotenv()
    pool = await get_pool()

    targets = {k: v for k, v in SCRAPERS.items() if k in universities}
    if not targets:
        print(f"No scrapers found for: {universities}. Available: {list(SCRAPERS)}")
        await pool.close()
        return

    for slug, scraper_class in targets.items():
        print(f"Running scraper: {slug}{' (force reset)' if force else ''}")
        scraper = scraper_class(pool, slug)
        scraper.use_cache = use_cache
        scraper.force_refresh = refresh
        try:
            count = await scraper.run(force=force)
            print(f"  {slug}: {count} courses upserted")
        except PermissionError as e:
            print(f"  {slug}: skipped — {e}")
        except Exception as e:
            print(f"  {slug}: failed — {e}")

    await pool.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run university course scrapers")
    parser.add_argument(
        "--university",
        action="append",
        dest="universities",
        metavar="SLUG",
        help="Scraper slug to run (repeatable). Defaults to all.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset queue and re-run discovery for the target universities.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_false",
        dest="use_cache",
        default=True,
        help="Disable local HTML snapshot caching.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh cached snapshots (bypass existing cache).",
    )
    args = parser.parse_args()

    universities = args.universities or list(SCRAPERS)
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    asyncio.run(main(universities, args.force, args.use_cache, args.refresh), loop_factory=loop_factory)

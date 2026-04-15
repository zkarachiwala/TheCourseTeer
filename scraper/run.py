import asyncio
import os
import sys

from dotenv import load_dotenv

from base_scraper import BaseScraper
from db import get_pool, upsert_course
from monash import MonashScraper
from rmit import RmitScraper

# Register per-university scrapers here as they are implemented (issues #4-8).
# Key is the university slug from the universities table.
SCRAPERS: dict[str, type[BaseScraper]] = {
    "rmit": RmitScraper,
    "monash": MonashScraper,
    # "uq": UqScraper,
    # "usyd": UsydScraper,
    # "unimelb": UnimelbScraper,
}


async def main() -> None:
    load_dotenv()
    pool = await get_pool()

    if not SCRAPERS:
        print("No scrapers registered. Add entries to SCRAPERS in run.py.")
        await pool.close()
        return

    for slug, scraper_class in SCRAPERS.items():
        print(f"Running scraper: {slug}")
        scraper = scraper_class(pool, slug)
        try:
            courses = await scraper.run()
            for course in courses:
                await upsert_course(pool, course)
            print(f"  {slug}: {len(courses)} courses upserted")
        except PermissionError as e:
            print(f"  {slug}: skipped — {e}")
        except Exception as e:
            print(f"  {slug}: failed — {e}")

    await pool.close()


if __name__ == "__main__":
    # psycopg3 requires SelectorEventLoop; Windows defaults to ProactorEventLoop.
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    asyncio.run(main(), loop_factory=loop_factory)

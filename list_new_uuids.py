import asyncio
import os
import sys
from dotenv import load_dotenv

# Add scraper to path
sys.path.append(os.path.join(os.getcwd(), "scraper"))

from db import get_pool

async def list_uuids():
    load_dotenv()
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, slug FROM campuses WHERE slug IN ('swinburne-prahran', 'swinburne-croydon', 'latrobe-mildura', 'latrobe-shepparton')")
            rows = await cur.fetchall()
            print("New Campus UUIDs:")
            for row in rows:
                print(f"  - {row[1]} ({row[2]}): {row[0]}")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(list_uuids())

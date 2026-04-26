import asyncio
import os
import sys
from dotenv import load_dotenv

# Add scraper to path
sys.path.append(os.path.join(os.getcwd(), "scraper"))

from db import get_pool

async def add_missing_campuses():
    load_dotenv()
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Get uni IDs
            await cur.execute("SELECT id, slug FROM universities WHERE slug IN ('swinburne', 'latrobe')")
            unis = {row[1]: row[0] for row in await cur.fetchall()}

            # Add Swinburne campuses
            swin_id = unis.get('swinburne')
            if swin_id:
                for name, slug in [('Croydon', 'swinburne-croydon'), ('Prahran', 'swinburne-prahran')]:
                    print(f"Adding Swinburne campus: {name}")
                    await cur.execute("""
                        INSERT INTO campuses (university_id, name, slug)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (university_id, slug) DO NOTHING
                    """, (swin_id, name, slug))

            # Add La Trobe campuses
            lat_id = unis.get('latrobe')
            if lat_id:
                for name, slug in [('Mildura', 'latrobe-mildura'), ('Shepparton', 'latrobe-shepparton')]:
                    print(f"Adding La Trobe campus: {name}")
                    await cur.execute("""
                        INSERT INTO campuses (university_id, name, slug)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (university_id, slug) DO NOTHING
                    """, (lat_id, name, slug))

    await pool.close()

if __name__ == "__main__":
    asyncio.run(add_missing_campuses())

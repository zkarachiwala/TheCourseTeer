import asyncio
import os
import json
import sys
from dotenv import load_dotenv

# Add scraper to path
sys.path.append(os.path.join(os.getcwd(), "scraper"))

from db import get_pool

async def check_db():
    load_dotenv()
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT u.slug, c.extraction_map 
                FROM site_configs c 
                JOIN universities u ON c.university_id = u.id 
                WHERE u.slug = 'swinburne'
            """)
            row = await cur.fetchone()
            if row:
                print(f"Uni: {row[0]}")
                print("Extraction Map:")
                print(json.dumps(row[1], indent=2))
            else:
                print("Swinburne config not found!")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(check_db())

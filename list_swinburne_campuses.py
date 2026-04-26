import asyncio
import os
import sys
from dotenv import load_dotenv

# Add scraper to path
sys.path.append(os.path.join(os.getcwd(), "scraper"))

from db import get_pool

async def list_campuses():
    load_dotenv()
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT c.id, c.name 
                FROM campuses c 
                JOIN universities u ON c.university_id = u.id 
                WHERE u.slug = 'swinburne'
            """)
            rows = await cur.fetchall()
            print("Swinburne Campuses in DB:")
            for row in rows:
                print(f"  - {row[1]}: {row[0]}")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(list_campuses())

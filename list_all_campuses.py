import asyncio
import os
import sys
from dotenv import load_dotenv

# Add scraper to path
sys.path.append(os.path.join(os.getcwd(), "scraper"))

from db import get_pool

async def list_all_campuses():
    load_dotenv()
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT u.slug, c.name 
                FROM campuses c 
                JOIN universities u ON c.university_id = u.id 
                WHERE u.slug IN ('monash', 'unimelb', 'rmit', 'swinburne', 'latrobe')
                ORDER BY u.slug, c.name
            """)
            rows = await cur.fetchall()
            current_uni = None
            for row in rows:
                if row[0] != current_uni:
                    current_uni = row[0]
                    print(f"\n{current_uni.upper()}:")
                print(f"  - {row[1]}")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(list_all_campuses())

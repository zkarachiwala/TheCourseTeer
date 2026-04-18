"""Quick DB check: list all scraped UniMelb courses with campus and ATAR."""
import asyncio
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


async def main():
    dsn = os.environ["DATABASE_URL"]
    async with await psycopg.AsyncConnection.connect(dsn) as conn:
        rows = await conn.execute(
            """
            SELECT c.name, c.duration_years,
                   string_agg(cam.name, ' + ' ORDER BY cam.name) AS campuses,
                   MAX(cc.atar_guaranteed) AS atar_g,
                   MAX(cc.atar_lowest_selection_rank) AS atar_r
            FROM courses c
            JOIN universities u ON u.id = c.university_id
            LEFT JOIN course_campuses cc ON cc.course_id = c.id
            LEFT JOIN campuses cam ON cam.id = cc.campus_id
            WHERE u.slug = 'unimelb'
            GROUP BY c.id, c.name, c.duration_years
            ORDER BY c.name
            """
        )
        results = await rows.fetchall()
    print(f"Total courses: {len(results)}\n")
    for r in results:
        print(f"  {r[0]:<60} {str(r[1])+'y':<6} {str(r[2]):<35} g={r[3]} r={r[4]}")


asyncio.run(main())

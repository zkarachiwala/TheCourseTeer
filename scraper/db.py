import os

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from models import CourseData


async def get_pool(dsn: str | None = None) -> AsyncConnectionPool:
    """Open and return an async connection pool. Reads DATABASE_URL from env if dsn omitted."""
    dsn = dsn or os.environ["DATABASE_URL"]
    pool = AsyncConnectionPool(dsn, open=False, kwargs={"prepare_threshold": None})
    await pool.open()
    return pool


async def get_university(pool: AsyncConnectionPool, slug: str) -> dict:
    """Return the universities row for slug. Raises KeyError if not found."""
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM universities WHERE slug = %s", (slug,)
            )
            row = await cur.fetchone()
    if row is None:
        raise KeyError(f"University not found: {slug}")
    return row


async def store_robots_rules(
    pool: AsyncConnectionPool, university_id: str, rules: dict
) -> None:
    """Persist parsed robots.txt rules to universities.robots_txt_rules."""
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE universities SET robots_txt_rules = %s WHERE id = %s",
            (Jsonb(rules), university_id),
        )


async def update_university_status(
    pool: AsyncConnectionPool, university_id: str, status: str
) -> None:
    """Update scraper_status and last_scraped_at for a university."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE universities
            SET scraper_status = %s, last_scraped_at = now()
            WHERE id = %s
            """,
            (status, university_id),
        )


async def get_campus_id(
    pool: AsyncConnectionPool, university_id: str, campus_slug: str
) -> str | None:
    """Return the campus uuid for the given university and campus slug, or None."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM campuses WHERE university_id = %s AND slug = %s",
                (university_id, campus_slug),
            )
            row = await cur.fetchone()
    return str(row[0]) if row else None


async def get_campus_map(
    pool: AsyncConnectionPool, university_id: str
) -> dict[str, str]:
    """Return {campus_name: campus_uuid} for the given university."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT name, id FROM campuses WHERE university_id = %s",
                (university_id,),
            )
            rows = await cur.fetchall()
    return {row[0]: str(row[1]) for row in rows}



async def upsert_course(pool: AsyncConnectionPool, course: CourseData) -> None:
    """Insert or update a course row, keyed on (university_id, source_url)."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO courses (
                university_id, name, source_url, faculty, campus_id,
                degree_type, duration_years,
                price_annual_csp_aud, price_annual_dfee_aud, csp_available,
                atar_guaranteed, atar_lowest_selection_rank, prerequisites
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (university_id, source_url) DO UPDATE SET
                name                       = EXCLUDED.name,
                faculty                    = EXCLUDED.faculty,
                campus_id                  = EXCLUDED.campus_id,
                degree_type                = EXCLUDED.degree_type,
                duration_years             = EXCLUDED.duration_years,
                price_annual_csp_aud       = EXCLUDED.price_annual_csp_aud,
                price_annual_dfee_aud      = EXCLUDED.price_annual_dfee_aud,
                csp_available              = EXCLUDED.csp_available,
                atar_guaranteed            = EXCLUDED.atar_guaranteed,
                atar_lowest_selection_rank = EXCLUDED.atar_lowest_selection_rank,
                prerequisites              = EXCLUDED.prerequisites,
                updated_at                 = now()
            """,
            (
                course.university_id,
                course.name,
                course.source_url,
                course.faculty,
                course.campus_id,
                course.degree_type,
                course.duration_years,
                course.price_annual_csp_aud,
                course.price_annual_dfee_aud,
                course.csp_available,
                course.atar_guaranteed,
                course.atar_lowest_selection_rank,
                Jsonb(course.prerequisites) if course.prerequisites is not None else None,
            ),
        )


async def get_or_create_run(
    pool: AsyncConnectionPool, university_id: str, force: bool = False
) -> dict:
    """Return the current in_progress run, or create a new one.

    If force=True, delete all scrape_queue rows for this university first,
    then always create a new run.
    """
    async with pool.connection() as conn:
        if force:
            await conn.execute(
                "DELETE FROM scrape_queue WHERE university_id = %s", (university_id,)
            )
        else:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT * FROM scrape_runs
                    WHERE university_id = %s AND status = 'in_progress'
                    ORDER BY run_number DESC LIMIT 1
                    """,
                    (university_id,),
                )
                row = await cur.fetchone()
            if row:
                return dict(row)

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO scrape_runs (university_id, run_number, forced)
                SELECT %s, COALESCE(MAX(run_number), 0) + 1, %s
                FROM scrape_runs WHERE university_id = %s
                RETURNING *
                """,
                (university_id, force, university_id),
            )
            return dict(await cur.fetchone())


async def mark_discovery_complete(pool: AsyncConnectionPool, run_id: str) -> None:
    """Mark discovery as complete for this run."""
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE scrape_runs SET discovery_complete = true WHERE id = %s",
            (run_id,),
        )


async def enqueue_urls(
    pool: AsyncConnectionPool, university_id: str, run_id: str, urls: list[str]
) -> None:
    """Insert URLs as pending queue entries. Skips duplicates (ON CONFLICT DO NOTHING)."""
    if not urls:
        return
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO scrape_queue (university_id, discovered_run_id, url)
                VALUES (%s, %s, %s)
                ON CONFLICT (university_id, url) DO NOTHING
                """,
                [(university_id, run_id, url) for url in urls],
            )


async def get_pending_urls(
    pool: AsyncConnectionPool, university_id: str, max_attempts: int = 3
) -> list[str]:
    """Return pending URLs for this university where attempt_count < max_attempts."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT url FROM scrape_queue
                WHERE university_id = %s
                  AND status = 'pending'
                  AND attempt_count < %s
                ORDER BY created_at
                """,
                (university_id, max_attempts),
            )
            rows = await cur.fetchall()
    return [row[0] for row in rows]


async def mark_url_complete(
    pool: AsyncConnectionPool, university_id: str, url: str, run_id: str
) -> None:
    """Mark a queue entry as complete."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE scrape_queue
            SET status = 'complete', completed_run_id = %s
            WHERE university_id = %s AND url = %s
            """,
            (run_id, university_id, url),
        )


async def mark_url_failed(
    pool: AsyncConnectionPool,
    university_id: str,
    url: str,
    error: str,
    max_attempts: int = 3,
) -> None:
    """Increment attempt count; set status='failed' once max_attempts is reached."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE scrape_queue
            SET attempt_count = attempt_count + 1,
                last_error = %s,
                status = CASE WHEN attempt_count + 1 >= %s THEN 'failed' ELSE 'pending' END
            WHERE university_id = %s AND url = %s
            """,
            (error, max_attempts, university_id, url),
        )


async def complete_run(pool: AsyncConnectionPool, run_id: str) -> None:
    """Mark a run as complete."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE scrape_runs
            SET status = 'complete', completed_at = now()
            WHERE id = %s
            """,
            (run_id,),
        )


async def upsert_selector(
    pool: AsyncConnectionPool,
    university_id: str,
    field_name: str,
    selector: str,
    ai_generated: bool,
    mode: str = "static",
) -> None:
    """Upsert a scraper_configs row for the given university + field."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO scraper_configs
                (university_id, field_name, selector, last_verified_at, ai_generated, mode)
            VALUES (%s, %s, %s, CASE WHEN %s THEN now() ELSE NULL END, %s, %s)
            ON CONFLICT (university_id, field_name) DO UPDATE SET
                selector         = EXCLUDED.selector,
                last_verified_at = EXCLUDED.last_verified_at,
                ai_generated     = EXCLUDED.ai_generated,
                mode             = EXCLUDED.mode
            """,
            (university_id, field_name, selector, ai_generated, ai_generated, mode),
        )

import pytest
from universal_engine import UniversalEngine
from models import CourseData

@pytest.mark.asyncio
async def test_migrate_unimelb(pool):
    """Verify that UniversalEngine can scrape a UniMelb course page with parity."""
    engine = UniversalEngine(pool)
    
    # 1. Get UniMelb ID and Config
    async with pool.connection() as conn:
        row = await conn.execute("SELECT id FROM universities WHERE slug = 'unimelb'")
        res = await row.fetchone()
        uni_id = str(res[0])
    
    config = await engine.get_config(uni_id)
    
    # 2. Use a real HTML sample (Computer Science course)
    # For a real integration test, we'd fetch it, but here we can mock with minimal HTML
    html = """
    <html>
        <h1>Bachelor of Computer Science</h1>
        <div>
            <p>Guaranteed ATAR 2026: 72.00</p>
            <p>Duration: 3 years full-time</p>
            <p>Campus: Parkville</p>
            <p>Commonwealth Supported Place (CSP) available</p>
            <p>VTAC code: 3200312345</p>
        </div>
    </html>
    """

    url = "https://study.unimelb.edu.au/find/courses/undergraduate/bachelor-of-computer-science/"
    
    # 3. Scrape
    course = await engine.scrape_page(html, config, url)
    
    # 4. Assert
    assert course.name == "Bachelor of Computer Science"
    assert course.duration_years == 3.0
    assert course.csp_available is True
    assert course.confidence_score >= 70
    
    assert len(course.campuses) == 1
    campus = course.campuses[0]
    assert campus.atar_guaranteed == 72
    assert "3200312345" in campus.admissions_codes

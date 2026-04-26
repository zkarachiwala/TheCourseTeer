import pytest
from universal_engine import UniversalEngine
from models import CourseData

@pytest.mark.asyncio
async def test_migrate_swinburne(pool):
    """Verify that UniversalEngine can scrape a Swinburne course page with parity."""
    engine = UniversalEngine(pool)
    
    # 1. Get Swinburne ID and Config
    async with pool.connection() as conn:
        row = await conn.execute("SELECT id FROM universities WHERE slug = 'swinburne'")
        res = await row.fetchone()
        uni_id = str(res[0])
    
    config = await engine.get_config(uni_id)
    
    # 2. Use a real HTML sample
    html = """
    <html>
        <h1>Bachelor of Design</h1>
        <div class="course-details__duration">
            <span class="domestic">3 years full-time</span>
        </div>
        <div class="course-details__campus">Hawthorn, Online</div>
        <div class="course-fees__block domestic">
            <h4 class="course-fees__sub-title">Guaranteed ATAR</h4>
            <p class="course-fees__total">70</p>
        </div>
        <div class="course-fees__block domestic">
            <h4 class="course-fees__sub-title">Estimated yearly fee</h4>
            <p class="course-fees__total">$9,500</p>
        </div>
        <div class="admissions-info">
            <p>VTAC code: 3400312345</p>
        </div>
    </html>
    """
    
    url = "https://www.swinburne.edu.au/course/undergraduate/bachelor-of-design/"
    
    # 3. Scrape
    course = await engine.scrape_page(html, config, url)
    
    # 4. Assert
    assert course.name == "Bachelor of Design"
    assert course.duration_years == 3.0
    assert course.csp_available is True
    
    # Check campuses
    # Current simple mapping will find "Hawthorn, Online" as location_str
    assert len(course.campuses) >= 1
    campus = course.campuses[0]
    assert "Hawthorn" in campus.campus_id
    assert campus.atar_guaranteed == 70
    assert "3400312345" in campus.admissions_codes

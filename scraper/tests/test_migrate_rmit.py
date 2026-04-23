import pytest
from universal_engine import UniversalEngine
from models import CourseData

@pytest.mark.asyncio
async def test_migrate_rmit(pool):
    """Verify that UniversalEngine can scrape an RMIT course page with parity."""
    engine = UniversalEngine(pool)
    
    # 1. Get RMIT ID and Config
    async with pool.connection() as conn:
        row = await conn.execute("SELECT id FROM universities WHERE slug = 'rmit'")
        res = await row.fetchone()
        uni_id = str(res[0])
    
    config = await engine.get_config(uni_id)
    
    # 2. Use a real HTML sample
    html = """
    <html>
        <head>
            <meta name="product_name" content="Bachelor of Software Engineering">
            <meta name="duration_domestic" content="Full-time 4 years, Part-time 8 years">
            <meta name="atar" content="2026 Guaranteed ATAR 80.00, ATAR 82.50*">
            <meta name="fees_domestic" content="Commonwealth Supported Place (CSP) available">
            <meta name="location_domestic" content="Melbourne City">
        </head>
        <body>
            <p>VTAC code: 3200377777</p>
        </body>
    </html>
    """
    
    url = "https://www.rmit.edu.au/study-with-us/levels-of-study/undergraduate-study/bachelor-degrees/bachelor-of-software-engineering"
    
    # 3. Scrape
    course = await engine.scrape_page(html, config, url)
    
    # 4. Assert
    assert course.name == "Bachelor of Software Engineering"
    assert course.duration_years == 4.0
    assert course.csp_available is True
    
    assert len(course.campuses) == 1
    campus = course.campuses[0]
    # For now, campus_id will be the extracted string "Melbourne City"
    assert "Melbourne City" in campus.campus_id
    # From "2026 Guaranteed ATAR 80.00, ATAR 82.50*"
    # Our parse_atar should return (80, 82)
    assert campus.atar_guaranteed == 80
    assert campus.atar_lowest_selection_rank == 82
    assert "3200377777" in campus.admissions_codes

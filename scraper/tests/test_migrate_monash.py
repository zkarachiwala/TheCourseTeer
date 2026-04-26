import pytest
from universal_engine import UniversalEngine
from models import CourseData

@pytest.mark.asyncio
async def test_migrate_monash(pool):
    """Verify that UniversalEngine can scrape a Monash course page with parity."""
    engine = UniversalEngine(pool)
    
    # 1. Get Monash ID and Config
    async with pool.connection() as conn:
        row = await conn.execute("SELECT id FROM universities WHERE slug = 'monash'")
        res = await row.fetchone()
        uni_id = str(res[0])
    
    config = await engine.get_config(uni_id)
    
    # 2. Use a real HTML sample (Computer Science course)
    html = """
    <html>
        <script type="application/ld+json">
        {
            "@type": "Course",
            "name": "Bachelor of Computer Science"
        }
        </script>
        <h1>Bachelor of Computer Science (wrong title)</h1>
        <table class="course-page__table-basic">
            <tr>
                <th>Duration:</th>
                <td>3 years (full-time)</td>
            </tr>
            <tr>
                <th>Location:</th>
                <td>On-campus at Clayton</td>
            </tr>
        </table>
        <div class="course-page__subject-req-item">
            <h2>75.00</h2>
            <p>Lowest selection rank</p>
        </div>
        <script>
            var dataLayer = [{"FeeDomesticCSP": "A$10,500"}];
        </script>
    </html>
    """
    
    url = "https://www.monash.edu/study/courses/find-a-course/courses/computer-science-c2001"
    
    # 3. Scrape
    course = await engine.scrape_page(html, config, url)
    
    # 4. Assert
    assert course.name == "Bachelor of Computer Science"
    assert course.duration_years == 3.0
    assert course.csp_available is True
    
    assert len(course.campuses) == 1
    campus = course.campuses[0]
    # For now, campus_id will be the extracted string "On-campus at Clayton" 
    # until we implement full campus mapping logic.
    assert "Clayton" in campus.campus_id
    assert campus.atar_lowest_selection_rank == 75

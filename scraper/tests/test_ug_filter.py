import pytest
import logging
from universal_engine import UniversalEngine
from models import SiteConfig, CourseData, CampusLink

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_ug_filter_by_name(pool):
    """
    REPRODUCTION: Verify that courses with PG-related keywords in their name are filtered out.
    """
    engine = UniversalEngine(pool)
    
    # Mock course data that should be filtered
    pg_courses = [
        "Master of Data Science",
        "Doctor of Philosophy",
        "Graduate Diploma in Education",
        "Graduate Certificate in Nursing",
        "Executive Master of Business Administration"
    ]
    
    for name in pg_courses:
        html = f"<html><h1>{name}</h1></html>"
        
        config = SiteConfig(
            id="test-uni",
            university_id="test-uni",
            base_url="https://test.edu",
            extraction_map={"name": {"selector": "h1"}},
            is_active=True
        )
        
        course_data = await engine.scrape_page(html, config, "https://test.edu")
        
        # This is expected to FAIL until the filter is implemented
        assert course_data is None, f"Course '{name}' should have been filtered out"

@pytest.mark.asyncio
async def test_ug_filter_by_degree_type(pool):
    """
    REPRODUCTION: Verify that courses identified as PG degree type are filtered out.
    """
    engine = UniversalEngine(pool)
    
    html = "<html><h1>Postgrad Course</h1><div id='level'>PG</div></html>"
    
    config = SiteConfig(
        id="test-uni",
        university_id="test-uni",
        base_url="https://test.edu",
        extraction_map={
            "name": {"selector": "h1"},
            "degree_type": {"selector": "#level"}
        },
        is_active=True
    )
    
    course_data = await engine.scrape_page(html, config, "https://test.edu")
    
    # This is expected to FAIL until the filter is implemented
    assert course_data is None, "Course with degree_type 'PG' should have been filtered out"

@pytest.mark.asyncio
async def test_ug_filter_keeps_undergrad(pool):
    """
    Verify that legitimate undergraduate courses are NOT filtered out.
    """
    engine = UniversalEngine(pool)
    
    html = "<html><h1>Bachelor of Science</h1><div id='level'>UG</div></html>"
    
    config = SiteConfig(
        id="test-uni",
        university_id="test-uni",
        base_url="https://test.edu",
        extraction_map={
            "name": {"selector": "h1"},
            "degree_type": {"selector": "#level"}
        },
        is_active=True
    )
    
    course_data = await engine.scrape_page(html, config, "https://test.edu")
    
    assert course_data is not None
    assert course_data.name == "Bachelor of Science"
    assert course_data.degree_type == "UG"

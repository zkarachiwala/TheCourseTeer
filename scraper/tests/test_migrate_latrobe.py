import pytest
import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from universal_engine import UniversalEngine
from models import SiteConfig, CourseData

_FIXTURES = Path(__file__).parent / "gold_standards" / "fixtures"

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_latrobe_migration_reproduction(pool):
    """
    Reproduction test for La Trobe migration.
    Attempts to scrape the sample La Trobe page using UniversalEngine with a 
    preliminary extraction map that mimics the legacy regex logic.
    """
    engine = UniversalEngine(pool)
    
    # Load the sample HTML
    sample_path = _FIXTURES / "latrobe_sample.html"
    if not sample_path.exists():
        pytest.skip("latrobe_sample.html not found")
        
    with open(sample_path, "r") as f:
        html = f.read()
        
    # Preliminary extraction map for La Trobe
    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "duration": {"regex": r'"duration"\s*:\s*"([0-9.]+)"'},
        "atar": {"regex": r'"minSelectionRankOffered"\s*:\s*"([0-9.]+)"'},
        "location": {
            "regex": r'"campuses"\s*:\s*(\[[^\]]+\])',
            "mapping": {
                "BU": "Bundoora",
                "ON": "Online"
            }
        },
        "admissions_codes": {"regex": r'"vtacCode"\s*:\s*(\d{9,10})'},
        "follow_urls": {"regex": r'/courses/data/2026/domestic/[a-z]+/bachelor-of-arts\?v=[0-9.]+'}
    }
    
    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b", # La Trobe UUID
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )
    
    # Mock fetch_fn
    async def mock_fetch(url):
        if "courses/data" in url:
            with open(_FIXTURES / "latrobe_detail_sample.json", "r") as f:
                return f.read()
        return ""

    # 1. Test basic extraction
    course_data = await engine.scrape_page(html, config, "https://www.latrobe.edu.au/courses/bachelor-of-arts", fetch_fn=mock_fetch)
    
    assert course_data.name == "Bachelor of Arts"
    assert course_data.duration_years == 3.0
    
    # Check campuses - should have multiple
    assert len(course_data.campuses) >= 2
    
    # Check campus mapping
    campus_ids = [c.campus_id for c in course_data.campuses]
    assert "Bundoora" in campus_ids
    assert "Online" in campus_ids
    
    # Check ATAR
    for campus in course_data.campuses:
        # Bachelor of arts at BU (Bundoora) has ATAR 55.50
        if "Bundoora" in campus.campus_id:
            assert campus.atar_lowest_selection_rank == 55.5

            # Check VTAC code for Bundoora
            assert "2100313021" in campus.admissions_codes

@pytest.mark.asyncio
async def test_latrobe_live_integration(pool):
    """Live integration test for La Trobe using UniversalEngine."""
    engine = UniversalEngine(pool, "latrobe")
    
    # 1. Fetch robots.txt and setup engine
    from http_client import make_client
    from robots import fetch_and_store_robots
    
    async with pool.connection() as conn:
        row = await conn.execute("SELECT id, homepage_url FROM universities WHERE slug = 'latrobe'")
        res = await row.fetchone()
        uni_id, homepage = str(res[0]), res[1]

    async with make_client() as client:
        rp = await fetch_and_store_robots(pool, uni_id, homepage, client)
        
        # 2. Test a real course URL
        url = "https://www.latrobe.edu.au/courses/bachelor-of-computer-science"
        # We use scrape_url which handles fetching and robots
        course = await engine.scrape_url(rp, url)
        
        assert course is not None
        assert "Computer Science" in course.name
        assert len(course.campuses) > 0
        
        # Check if we got ATARs or VTAC codes
        # Note: VTAC codes are often null in La Trobe's data endpoints (e.g. Computer Science 2026)
        # So we just log whether we found any
        has_codes = any(len(c.admissions_codes) > 0 for c in course.campuses)
        logger.info(f"Extracted admissions codes: {has_codes}")

@pytest.mark.asyncio
async def test_latrobe_unescape_name(pool):
    """Verify that UniversalEngine unescapes JSON slashes in course names."""
    engine = UniversalEngine(pool, "latrobe")
    
    html = '<html><script>window.courseData = {"advertisedTitle": "Bachelor of Commerce\\/Bachelor of Biomedicine", "campuses": ["BU"], "duration": "4"};</script></html>'
    
    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "duration": {"regex": r'"duration"\s*:\s*"([0-9.]+)"'},
        "location": {"regex": r'"campuses"\s*:\s*(\[[^\]]+\])'}
    }
    
    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b",
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )
    
    course_data = await engine.scrape_page(html, config, "https://test.edu")
    
    # It should be unescaped
    assert course_data.name == "Bachelor of Commerce/Bachelor of Biomedicine"

@pytest.mark.asyncio
async def test_latrobe_accounting_gold_standard(pool):
    """
    Gold-standard test for La Trobe Bachelor of Accounting.
    Verifies exact ATAR values for specific campuses.
    """
    engine = UniversalEngine(pool)
    
    # Load the sample HTML
    sample_path = _FIXTURES / "latrobe_accounting_sample.html"
    if not sample_path.exists():
        pytest.skip("latrobe_accounting_sample.html not found")
        
    with open(sample_path, "r") as f:
        html = f.read()
        
    # Extraction map for La Trobe
    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "duration": {"regex": r'"duration"\s*:\s*"([0-9.]+)"'},
        "atar": {
            "regex": r'"minSelectionRankOffered"\s*:\s*"([0-9.]+)"',
            "json_regex": r'"allAtars"\s*:\s*({.*?}),\s*"ugRseAtarPrereqReqmt"',
            "json_path": "latest_key"
        },
        "location": {
            "regex": r'"campuses"\s*:\s*(\[[^\]]+\])',
            "mapping": {
                "BU": "Bundoora",
                "BE": "Bendigo",
                "AW": "Albury-Wodonga",
                "MI": "Mildura",
                "SH": "Shepparton",
                "ON": "Online"
            }
        },
        "admissions_codes": {"regex": r'"vtacCode"\s*:\s*(\d{9,10})'},
        "follow_urls": {"regex": r'/courses/data/2026/domestic/[a-z]+/bachelor-of-accounting\?v=[0-9.]+'}
    }

    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b",
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )

    # Mock fetch_fn
    async def mock_fetch(url):
        if "courses/data" in url:
            with open(_FIXTURES / "latrobe_accounting_detail.json", "r") as f:
                return f.read()
        return ""

    # Map for campus IDs to aliases used in allAtars
    code_map = {
        "bu": "Bundoora",
        "be": "Bendigo",
        "aw": "Albury-Wodonga",
        "mi": "Mildura",
        "sh": "Shepparton",
        "on": "Online"
    }

    course_data = await engine.scrape_page(
        html, 
        config, 
        "https://www.latrobe.edu.au/courses/bachelor-of-accounting", 
        code_map=code_map,
        fetch_fn=mock_fetch
    )
    assert "Bachelor of Accounting" in course_data.name
    
    # Check ATARs for specific campuses
    campuses_found = {c.campus_id: c.atar_lowest_selection_rank for c in course_data.campuses}
    
    # Assertions from task:
    # Melbourne (Bundoora): 61.90
    # Bendigo: 60.25
    # Online: 61.10
    
    assert "Bundoora" in campuses_found
    assert campuses_found["Bundoora"] == 61.90
    
    assert "Bendigo" in campuses_found
    assert campuses_found["Bendigo"] == 60.25

    assert "Online" in campuses_found
    assert campuses_found["Online"] == 61.10

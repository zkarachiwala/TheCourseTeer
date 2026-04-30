import pytest
import os
import json
import logging
from bs4 import BeautifulSoup
from universal_engine import UniversalEngine
from models import SiteConfig, CourseData

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_latrobe_unescape_name(pool):
    """
    REPRODUCTION: Verify that UniversalEngine unescapes JSON slashes in course names.
    """
    engine = UniversalEngine(pool)
    
    # We'll use a mock HTML snippet to trigger the unescaping logic
    html = '<html><script>window.courseData = {"advertisedTitle": "Bachelor of Commerce\\\\/Bachelor of Biomedicine", "campuses": ["BU"], "duration": "4"};</script></html>'
    
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
    
    # If the engine sees 'Bachelor of Commerce\/Bachelor of Biomedicine'
    # and doesn't unescape it, this will fail.
    assert course_data.name == "Bachelor of Commerce/Bachelor of Biomedicine"

@pytest.mark.asyncio
async def test_latrobe_atar_extraction_from_sample(pool):
    """
    REPRODUCTION: Verify that ATAR is extracted correctly from the nested JSON structure.
    """
    engine = UniversalEngine(pool)
    
    # Load the local sample
    sample_path = "../latrobe_sample.html"
    if not os.path.exists(sample_path):
        pytest.skip(f"{sample_path} not found")
        
    with open(sample_path, "r") as f:
        html = f.read()
        
    # Current brittle extraction map (needs update)
    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "atar": {"regex": r'"minSelectionRankOffered"\s*:\s*"([0-9.]+)"'},
        "location": {"regex": r'"campuses"\s*:\s*(\[[^\]]+\])', "mapping": {"BU": "8841ca47-be65-4697-a49b-ed738259a315"}}
    }
    
    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b",
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )
    
    course_data = await engine.scrape_page(html, config, "https://www.latrobe.edu.au/courses/bachelor-of-animal-and-veterinary-biosciences")
    
    # Check if we got the ATAR for Bundoora
    assert len(course_data.campuses) > 0
    bu_campus = next((c for c in course_data.campuses if "8841ca47-be65-4697-a49b-ed738259a315" in c.campus_id), None)
    assert bu_campus is not None
    # We expect this to fail because current regex might pick up nothing or wrong value
    assert bu_campus.atar_lowest_selection_rank is not None
    assert bu_campus.atar_lowest_selection_rank == 60.25

@pytest.mark.asyncio
async def test_latrobe_duration_extraction(pool):
    """
    REPRODUCTION: Verify duration extraction from latrobe_sample.html.
    """
    engine = UniversalEngine(pool)
    
    sample_path = "../latrobe_sample.html"
    with open(sample_path, "r") as f:
        html = f.read()
        
    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "duration": {
            "anchor": "Duration", 
            "regex": r'("duration"\s*:\s*"?([0-9.]+)"?|Duration.*?\b(\d+(?:\.\d+)?)\s*years?)'
        }
    }
    
    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b",
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )
    
    course_data = await engine.scrape_page(html, config, "https://test.edu")
    
    # Expected duration for Animal and Veterinary Biosciences is 3 years
    assert course_data.duration_years == 3.0

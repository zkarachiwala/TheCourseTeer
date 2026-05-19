import pytest
import os
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from universal_engine import UniversalEngine
from models import SiteConfig, CourseData

_FIXTURES = Path(__file__).parent / "gold_standards" / "fixtures"

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
    sample_path = _FIXTURES / "latrobe_sample.html"
    if not sample_path.exists():
        pytest.skip("latrobe_sample.html fixture not found")
        
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
    # Fixture is Bachelor of Arts — BU lowest selection rank is 55.50
    assert bu_campus.atar_lowest_selection_rank is not None
    assert bu_campus.atar_lowest_selection_rank == 55.5

@pytest.mark.asyncio
async def test_latrobe_duration_extraction(pool):
    """
    REPRODUCTION: Verify duration extraction from latrobe_sample.html.
    """
    engine = UniversalEngine(pool)
    
    sample_path = _FIXTURES / "latrobe_sample.html"
    if not sample_path.exists():
        pytest.skip("latrobe_sample.html fixture not found")
    with open(sample_path, "r") as f:
        html = f.read()
        
    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "duration": {"regex": r'"duration"\s*:\s*"([0-9.]+)"'}
    }

    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b",
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )

    course_data = await engine.scrape_page(html, config, "https://test.edu")

    # Fixture is Bachelor of Arts — 3 years
    assert course_data.duration_years == 3.0


@pytest.mark.asyncio
async def test_latrobe_atar_multi_alias_campus(pool):
    """
    REGRESSION: Campus with multiple alias codes (e.g. Online has both "on"
    and "ot") must still resolve ATAR. Dict inversion previously lost one alias.
    """
    ON_UUID = "fa65309e-488e-4278-bc13-5e720e8a8b3d"
    engine = UniversalEngine(pool)
    html = (
        '<html><script>window.courseData = {'
        '"advertisedTitle": "Bachelor of Business",'
        '"campuses": ["ON"],'
        '"duration": "3",'
        '"allAtars": {"2027": {"ON": {"minSelectionRankOffered": "66.9",'
        '"aspireMinimumATAR": ""}}}, "ugRse": null'
        '};</script></html>'
    )

    extraction_map = {
        "name": {"regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'},
        "duration": {"regex": r'"duration"\s*:\s*"([0-9.]+)"'},
        "location": {
            "regex": r'"campuses"\s*:\s*(\[[^\]]+\])',
            "mapping": {"ON": ON_UUID},
        },
        "atar": {
            "json_regex": r'"allAtars"\s*:\s*(\{.*?\})\s*,\s*"ugRse',
            "json_path": "latest_key",
        },
    }

    # code_map has both "on" and "ot" pointing to the same Online UUID.
    # Without the fix, dict inversion kept only "ot", so atar_map.get("OT")
    # returned None and the ATAR was lost.
    code_map = {
        "on": ON_UUID,
        "ot": ON_UUID,
    }

    config = SiteConfig(
        id="f5b3d349-0214-480b-89bc-7b70298e722b",
        university_id="f5b3d349-0214-480b-89bc-7b70298e722b",
        base_url="https://www.latrobe.edu.au",
        extraction_map=extraction_map,
        is_active=True,
    )

    course_data = await engine.scrape_page(
        html, config, "https://test.edu", code_map=code_map
    )

    assert course_data is not None
    on_campus = next(
        (c for c in course_data.campuses if c.campus_id == ON_UUID), None
    )
    assert on_campus is not None, "Online campus not found"
    assert on_campus.atar_lowest_selection_rank == 66.9

"""
Gold-standard tests for La Trobe University scraper.

All expected values have been manually verified against the La Trobe website
(May 2026). Fixtures are saved HTML/JSON snapshots of the live pages.
"""
import pytest
from pathlib import Path
from universal_engine import UniversalEngine
from models import SiteConfig

_FIXTURES = Path(__file__).parent / "gold_standards" / "fixtures"

_UNI_ID = "f5b3d349-0214-480b-89bc-7b70298e722b"

_EXTRACTION_MAP = {
    "name": {
        "regex": r'"advertisedTitle"\s*:\s*"([^"]+)"'
    },
    "duration": {
        "regex": r'"duration"\s*:\s*"([0-9.]+)"'
    },
    "atar": {
        "json_regex": r'"allAtars"\s*:\s*(\{.*?\})\s*,\s*"ugRse',
        "json_path": "latest_key"
    },
    "location": {
        "regex": r'"campuses"\s*:\s*(\[[^\]]+\])',
        "mapping": {
            "BU": "8841ca47-be65-4697-a49b-ed738259a315",
            "ON": "fa65309e-488e-4278-bc13-5e720e8a8b3d",
            "AW": "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0",
            "WO": "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0",
            "BE": "37a8e2ca-1643-48a5-85b1-6b91cc0bc15a",
            "MC": "b53c0416-8f3e-4a91-869d-f53d300cd8db",
            "MI": "cae2929f-5cda-4100-a542-85ae4ea327fb",
            "SH": "c97655c5-37de-4aaa-89da-923f264a1741",
            "SY": "b53c0416-8f3e-4a91-869d-f53d300cd8db",
            "CI": "b53c0416-8f3e-4a91-869d-f53d300cd8db",
        }
    },
    "admissions_codes": {"regex": r'"vtacCode"\s*:\s*(\d{9,10})'},
    "follow_urls": {"regex": r"/courses/data/202[6-9]/domestic/[a-z]+/[^'\"\s]+"}
}

_CODE_MAP = {
    "bu": "8841ca47-be65-4697-a49b-ed738259a315",
    "on": "fa65309e-488e-4278-bc13-5e720e8a8b3d",
    "aw": "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0",
    "wo": "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0",
    "be": "37a8e2ca-1643-48a5-85b1-6b91cc0bc15a",
    "mc": "b53c0416-8f3e-4a91-869d-f53d300cd8db",
    "mi": "cae2929f-5cda-4100-a542-85ae4ea327fb",
    "sh": "c97655c5-37de-4aaa-89da-923f264a1741",
    "sy": "b53c0416-8f3e-4a91-869d-f53d300cd8db",
}

BU = "8841ca47-be65-4697-a49b-ed738259a315"
BE = "37a8e2ca-1643-48a5-85b1-6b91cc0bc15a"
WO = "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0"
MI = "cae2929f-5cda-4100-a542-85ae4ea327fb"
SH = "c97655c5-37de-4aaa-89da-923f264a1741"
ON = "fa65309e-488e-4278-bc13-5e720e8a8b3d"


def _config():
    return SiteConfig(
        id=_UNI_ID,
        university_id=_UNI_ID,
        base_url="https://www.latrobe.edu.au",
        extraction_map=_EXTRACTION_MAP,
        is_active=True,
    )


def _make_fetch_fn(fixture_prefix: str):
    """Return a mock fetch_fn that serves detail JSON fixtures by campus code."""
    async def fetch_fn(url: str) -> str:
        campus = url.split("/domestic/")[1].split("/")[0].lower()
        path = _FIXTURES / f"{fixture_prefix}_detail_{campus}.json"
        if path.exists():
            return path.read_text()
        return ""
    return fetch_fn


@pytest.mark.asyncio
async def test_latrobe_bachelor_of_nursing(pool):
    """
    Gold standard: Bachelor of Nursing.
    Verified May 2026 against latrobe.edu.au.
    Expects: 3 years, 5 campuses, per-campus ATARs.
    """
    sample = _FIXTURES / "latrobe_bachelor_of_nursing_sample.html"
    if not sample.exists():
        pytest.skip("latrobe_bachelor_of_nursing_sample.html not found")

    engine = UniversalEngine(pool)
    course = await engine.scrape_page(
        sample.read_text(),
        _config(),
        "https://www.latrobe.edu.au/courses/bachelor-of-nursing",
        code_map=_CODE_MAP,
        fetch_fn=_make_fetch_fn("latrobe_bachelor_of_nursing"),
    )

    assert course is not None
    assert "Bachelor of Nursing" in course.name
    assert course.duration_years == 3.0

    campus_atars = {c.campus_id: c.atar_lowest_selection_rank for c in course.campuses}
    assert campus_atars.get(BU) == 70.15
    assert campus_atars.get(WO) == 64.55
    assert campus_atars.get(BE) == 63.60
    assert campus_atars.get(MI) == 63.30
    assert campus_atars.get(SH) == 57.85


@pytest.mark.asyncio
async def test_latrobe_bachelor_of_criminology(pool):
    """
    Gold standard: Bachelor of Criminology.
    Verified May 2026 against latrobe.edu.au.
    Expects: 3 years, BU/BE/ON campuses, ATARs for BU and BE, none for Online.
    """
    sample = _FIXTURES / "latrobe_bachelor_of_criminology_sample.html"
    if not sample.exists():
        pytest.skip("latrobe_bachelor_of_criminology_sample.html not found")

    engine = UniversalEngine(pool)
    course = await engine.scrape_page(
        sample.read_text(),
        _config(),
        "https://www.latrobe.edu.au/courses/bachelor-of-criminology",
        code_map=_CODE_MAP,
        fetch_fn=_make_fetch_fn("latrobe_bachelor_of_criminology"),
    )

    assert course is not None
    assert "Bachelor of Criminology" in course.name
    assert course.duration_years == 3.0

    campus_atars = {c.campus_id: c.atar_lowest_selection_rank for c in course.campuses}
    assert campus_atars.get(BU) == 55.3
    assert campus_atars.get(BE) == 55.65
    assert campus_atars.get(ON) is None


@pytest.mark.asyncio
async def test_latrobe_bachelor_of_biomedical_science(pool):
    """
    Gold standard: Bachelor of Biomedical Science.
    Verified May 2026 against latrobe.edu.au.
    Expects: 3 years, WO/BE campuses, ATARs for both.
    """
    sample = _FIXTURES / "latrobe_biomedical_sample.html"
    if not sample.exists():
        pytest.skip("latrobe_biomedical_sample.html not found")

    engine = UniversalEngine(pool)
    course = await engine.scrape_page(
        sample.read_text(),
        _config(),
        "https://www.latrobe.edu.au/courses/bachelor-of-biomedical-science",
        code_map=_CODE_MAP,
        fetch_fn=_make_fetch_fn("latrobe_biomedical"),
    )

    assert course is not None
    assert "Biomedical Science" in course.name
    assert course.duration_years == 3.0

    campus_atars = {c.campus_id: c.atar_lowest_selection_rank for c in course.campuses}
    assert campus_atars.get(WO) == 60.55
    assert campus_atars.get(BE) == 59.05

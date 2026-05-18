import pytest
import os
from pathlib import Path
from universal_engine import UniversalEngine
from models import SiteConfig

_FIXTURES = Path(__file__).parent / "gold_standards" / "fixtures"


@pytest.mark.asyncio
async def test_federation_nursing_gold_standard(pool):
    """
    Gold-standard test for Federation University Bachelor of Nursing.
    Verifies exact ATAR values and campus mappings.
    """
    engine = UniversalEngine(pool)

    # Load the sample HTML
    sample_path = _FIXTURES / "federation_nursing_sample.html"
    if not sample_path.exists():
        pytest.skip("federation_nursing_sample.html not found")

    with open(sample_path, "r") as f:
        html = f.read()

    # Extraction map for Federation University
    extraction_map = {
        "name": {"selector": "title", "regex": r"^([^|]+?)\s*\|"},
        "duration": {"regex": r'"heading"\s*:\s*"Duration"\s*,\s*"summary"\s*:\s*"([^"]+)"'},
        "atar": {"regex": r'"heading"\s*:\s*"ATAR"\s*,\s*"summary"\s*:\s*"([^"]+)"'},
        "fees": {"regex": r'Commonwealth Supported Place'},
        "location": {
            "regex": r'"heading"\s*:\s*"Locations"\s*,\s*"summary"\s*:\s*"([^"]+)"',
            "mapping": {
                "Ballarat":  "e84c817b-c88d-4211-801b-7f97009f0370",
                "Mt Helen":  "e84c817b-c88d-4211-801b-7f97009f0370",
                "Gippsland": "87036014-4081-4075-bbed-784bb926a788",
                "Churchill": "87036014-4081-4075-bbed-784bb926a788",
                "Berwick":   "c89c9c6b-4a6b-442e-801c-1073fa69b8fd",
                "Online":    "e9649dc5-7636-4822-8d34-e192fc1bf195"
            }
        },
        "admissions_codes": {"regex": r"(37\d{8})"}
    }

    config = SiteConfig(
        id="ea176745-a7d0-4773-b9dc-c08624754035",
        university_id="ea176745-a7d0-4773-b9dc-c08624754035",
        base_url="https://www.federation.edu.au",
        extraction_map=extraction_map,
        is_active=True
    )

    course_data = await engine.scrape_page(
        html,
        config,
        "https://www.federation.edu.au/courses/dnn5-bachelor-of-nursing/"
    )

    assert course_data is not None
    assert "Bachelor of Nursing" in course_data.name
    assert course_data.duration_years == 3.0
    assert course_data.csp_available is True

    # Check campuses — Ballarat Mt Helen, Gippsland Churchill, Berwick (Mt Helen deduplicates into Ballarat)
    campus_ids = {c.campus_id for c in course_data.campuses}
    assert "e84c817b-c88d-4211-801b-7f97009f0370" in campus_ids  # Ballarat Mt Helen
    assert "87036014-4081-4075-bbed-784bb926a788" in campus_ids  # Gippsland Churchill
    assert "c89c9c6b-4a6b-442e-801c-1073fa69b8fd" in campus_ids  # Berwick

    # Each campus gets the same global ATAR
    for campus in course_data.campuses:
        assert campus.atar_guaranteed == 60.0
        assert campus.atar_lowest_selection_rank == 50.0

    # VTAC codes are assigned globally to all campuses — check known per-campus codes are present
    all_codes = {code for c in course_data.campuses for code in c.admissions_codes}
    assert "3702410331" in all_codes  # Ballarat (blended)
    assert "3702610331" in all_codes  # Berwick (blended)
    assert "3702510331" in all_codes  # Gippsland (blended)
    assert "3700510331" in all_codes  # Mt Helen (on campus)

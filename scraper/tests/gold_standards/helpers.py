"""Shared utilities for gold-standard fixture tests."""
import sys
from pathlib import Path

# Ensure scraper/ is on sys.path so imports work when running from any directory
_scraper_dir = Path(__file__).parent.parent.parent
if str(_scraper_dir) not in sys.path:
    sys.path.insert(0, str(_scraper_dir))

from models import SiteConfig
from seed_site_configs import SITE_CONFIGS, UNI_MAP

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def make_config(slug: str) -> SiteConfig:
    """Build a SiteConfig for the given slug from the canonical SITE_CONFIGS list."""
    uni_id = UNI_MAP[slug]
    cfg_dict = next(c for c in SITE_CONFIGS if c["university_id"] == uni_id)
    return SiteConfig(
        id="00000000-0000-0000-0000-000000000001",
        university_id=uni_id,
        base_url=cfg_dict["base_url"],
        extraction_map=cfg_dict["extraction_map"],
        robots_txt_status=cfg_dict.get("robots_txt_status"),
        notes=cfg_dict.get("notes"),
    )


def load_fixture(filename: str) -> str:
    """Load a fixture file from the fixtures/ directory and return its text."""
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Fixture not found: {path}\n"
            f"Capture it with: curl -A 'Mozilla/5.0' -s '<url>' > scraper/tests/gold_standards/fixtures/{filename}"
        )
    return path.read_text(encoding="utf-8")

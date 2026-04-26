from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CampusLink:
    """Campus association for a course, with optional campus-specific ATAR."""

    campus_id: str
    atar_guaranteed: int | None = None
    atar_lowest_selection_rank: int | None = None
    extraction_notes: str | None = None
    admissions_codes: list[str] = field(default_factory=list)
    confidence_score: int | None = None


@dataclass
class CourseData:
    """A single course record to be upserted into the courses table."""

    university_id: str
    name: str
    source_url: str
    faculty: str | None = None
    campuses: list[CampusLink] = field(default_factory=list)
    degree_type: str | None = None
    duration_years: float | None = None
    price_annual_csp_aud: int | None = None
    price_annual_dfee_aud: int | None = None
    csp_available: bool | None = None
    prerequisites: list[str] | None = None
    confidence_score: int | None = None


@dataclass
class SiteConfig:
    """Configuration for a university scraper."""

    id: str
    university_id: str
    base_url: str
    extraction_map: dict[str, Any]
    robots_txt_status: str | None = None
    version: int = 1
    is_active: bool = True
    sample_urls: list[str] = field(default_factory=list)
    notes: str | None = None
    last_updated: datetime | None = None
    created_at: datetime | None = None

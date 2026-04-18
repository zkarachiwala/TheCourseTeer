from dataclasses import dataclass, field


@dataclass
class CampusLink:
    """Campus association for a course, with optional campus-specific ATAR."""

    campus_id: str
    atar_guaranteed: int | None = None
    atar_lowest_selection_rank: int | None = None
    extraction_notes: str | None = None


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

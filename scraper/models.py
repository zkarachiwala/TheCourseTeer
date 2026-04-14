from dataclasses import dataclass


@dataclass
class CourseData:
    """A single course record to be upserted into the courses table."""

    university_id: str
    name: str
    source_url: str
    faculty: str | None = None
    campus_id: str | None = None
    degree_type: str | None = None
    duration_years: float | None = None
    price_annual_csp_aud: int | None = None
    price_annual_dfee_aud: int | None = None
    csp_available: bool | None = None
    atar_guaranteed: int | None = None
    atar_lowest_selection_rank: int | None = None
    prerequisites: list[str] | None = None

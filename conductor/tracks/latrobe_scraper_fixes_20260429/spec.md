# Specification: Fix La Trobe Scraper Issues & Undergraduate Filter (2026-04-29)

## Problem Description
The La Trobe University scraper (via `UniversalEngine`) has several issues. Additionally, we need to enforce a strict "Undergraduate Only" policy across all scrapers to prevent postgraduate data from polluting the database.

1. **Title Unescaping:** Double major names containing slashes (e.g., `Bachelor of Laws\/Bachelor of Criminology`) are still appearing with backslashes.
2. **Missing ATARs:** Brittle regex doesn't handle nested JSON structure (`allAtars`).
3. **Incomplete Duration Extraction:** Needs more robust patterns.
4. **Postgraduate Pollution:** Postgraduate courses (Masters, Doctorates, Graduate Diplomas, etc.) are being scraped and stored. These are explicitly **OUT OF SCOPE**.

## Goals
- Fix `UniversalEngine` to robustly unescape JSON-style strings.
- Implement specialized handling in `UniversalEngine` for La Trobe's `allAtars` JSON data.
- **Implement a mandatory Undergraduate filter** in `UniversalEngine` that drops any course not identified as undergraduate.
- Update `SITE_CONFIGS` for La Trobe to improve extraction and ensure course levels are correctly identified.
- Verify extraction with existing `latrobe_sample.html`.

## Technical Details
- **Engine:** `UniversalEngine` in `scraper/universal_engine.py`.
- **Filtering Logic:** 
  - Enhance `UniversalEngine` to check `degree_type` (or a dedicated `course_level` field).
  - If the level is identified as "PG", "Masters", "Doctorate", "Graduate Diploma", etc., the course must be discarded before it reaches the `upsert` phase.
- **Key Changes:**
  - Enhance `_extract_field` for better unescaping.
  - Handle structured JSON objects in `_extract_field` for fields like `atar`.
  - Add `should_skip_course(course_data)` logic to `UniversalEngine`.

## Acceptance Criteria
- [ ] `test_latrobe_unescape_name` passes with correctly unescaped slashes.
- [ ] `test_latrobe_atar_extraction` successfully extracts the ATAR (60.25) for Bundoora from `latrobe_sample.html`.
- [ ] **UG Filter Test:** A course identified as "PG" or containing "Masters" in the name is NOT added to the database.
- [ ] Acceptance test verifies that a Masters course from La Trobe is filtered out during a test run.

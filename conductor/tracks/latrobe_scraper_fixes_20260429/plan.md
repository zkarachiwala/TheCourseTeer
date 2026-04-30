# Implementation Plan: Fix La Trobe Scraper & Implement UG-Only Filter

This track fixes La Trobe-specific extraction issues and implements a global undergraduate-only filter for the universal scraper engine.

## Phase 1: Research & Reproduction (TDD Start)
- [ ] Create `scraper/tests/test_latrobe_fixes.py` with failing tests for:
    - Slash unescaping in names.
    - ATAR extraction from the `allAtars` JSON structure in `latrobe_sample.html`.
    - Duration extraction from `latrobe_sample.html`.
- [ ] Create `scraper/tests/test_ug_filter.py` with failing tests for:
    - Filtering out courses with "Masters" in the name.
    - Filtering out courses with "Doctor" in the name.
    - Filtering out courses with "Graduate Diploma" or "Graduate Certificate" in the name.
    - Filtering out courses where `degree_type` is explicitely "PG".

## Phase 2: Core Engine Enhancements (`universal_engine.py`)
- [ ] Improve `_extract_field` to handle robust JSON unescaping and structured JSON values.
- [ ] Implement `should_skip_course(course_data)` method in `UniversalEngine`.
- [ ] Integrate the skip logic into the main `scrape_page` or `scrape_url` flow.

## Phase 3: Configuration Updates (`seed_site_configs.py`)
- [ ] Update La Trobe's `extraction_map` to use the improved patterns.
- [ ] Ensure `courseLevelCode` is correctly mapped to `degree_type` for La Trobe.

## Phase 4: Validation & Cleanup
- [ ] Run all tests in the worktree.
- [ ] Perform a manual verification run against `latrobe_sample.html`.
- [ ] Verify that no PG courses are present in a fresh scrape (simulated or real).

[checkpoint: end-of-Phase-1]
[checkpoint: end-of-Phase-2]
[checkpoint: end-of-Phase-3]
[checkpoint: end-of-Phase-4]

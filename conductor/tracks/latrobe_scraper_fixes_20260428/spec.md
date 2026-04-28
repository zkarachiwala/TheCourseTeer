# Specification: Fix La Trobe Scraper Issues

## Problem Description
The La Trobe University scraper (via `UniversalEngine`) is failing to correctly extract and format several key data points:
1. **Double Major Names:** Course names containing slashes (e.g., `Bachelor of Laws\/Bachelor of Criminology`) are not being properly unescaped.
2. **Missing ATARs:** No courses are currently showing ATAR values, likely due to regex mismatches or changes in the data structure.
3. **Missing Durations:** Some courses are missing duration information.

## Goals
- Ensure all course names are properly unescaped and formatted.
- Successfully extract ATAR (Minimum Selection Rank) for all applicable courses and campuses.
- Ensure course duration is extracted correctly.
- Use existing local cache/samples where possible for validation.

## Technical Details
- **Engine:** `UniversalEngine` in `scraper/universal_engine.py`.
- **Configuration:** `SITE_CONFIGS` in `scraper/seed_site_configs.py`.
- **Key Fields to Fix:**
  - `name`: Needs robust JSON-style unescaping.
  - `atar`: Update regex to match La Trobe's JSON data structure (`minSelectionRankOffered`).
  - `duration`: Update regex or selection logic.

## Acceptance Criteria
- [ ] `test_latrobe_unescape_name` passes with correctly unescaped slashes.
- [ ] `test_latrobe_migration_reproduction` passes and correctly extracts ATAR values.
- [ ] Live integration test verifies duration extraction for a known course.

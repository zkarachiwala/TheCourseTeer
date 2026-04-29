# Implementation Plan: Fix La Trobe Scraper Issues

## Phase 1: Research & Reproduction
- [x] Reproduce the unescaping issue using `test_latrobe_unescape_name` (Verified working in code, but still reported as issue)
- [x] Reproduce the missing ATAR/Duration issues using `test_latrobe_migration_reproduction` (Skipped - samples missing, proceeding with fix)

## Phase 2: Core Engine Fixes
- [x] Improve `_extract_field` in `universal_engine.py` to handle more robust unescaping.
- [x] Refine `_parse_atar` and `_parse_duration` to handle edge cases and non-string inputs if necessary.
- [x] Add name extraction fallback and duration inference from credit points.
- [x] Filter out non-course pages in `UniversalEngine`.
- [x] Log ATAR extraction failures to `atar_issues` table.

## Phase 3: Configuration Updates
- [x] Update `SITE_CONFIGS` in `seed_site_configs.py` for La Trobe:
  - Make regex for `name`, `duration`, and `atar` more flexible (handle optional quotes).
  - Ensure `follow_urls` regex is correct.
  - Update discovery to prioritize main course pages for ATAR extraction.
  - Add missing campus mappings (`OT`, `CI`, `SY`, `WO`, `SH`).

## Phase 4: Web Application Updates
- [x] Add dynamic routes for university slugs (e.g., `/rmit`, `/latrobe`).
- [x] Support pre-filtering in `CourseListClient`.

## Phase 5: Validation
- [ ] Run a fresh HTML-based rescrape for La Trobe and verify results.

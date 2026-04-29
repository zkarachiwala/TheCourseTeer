# Specification: La Trobe Scraper Validation & Fixes

## Context
The La Trobe scraper was migrated to the `UniversalEngine` but hasn't been fully validated. Basic extraction works, but key data points (VTAC codes) are missing from the JSON data layer, and development artifacts (samples) are missing from the repo.

## Success Criteria
1.  **Reproduction Samples Restored:** `latrobe_sample.html` and `latrobe_detail_sample.json` exist and are current.
2.  **VTAC Code Extraction Fixed:** The scraper reliably finds admissions codes either in the JSON layer or the main HTML page.
3.  **Campus-ATAR Mapping Validated:** Selection ranks are correctly associated with their respective campuses (Bundoora, Bendigo, Albury-Wodonga, City, etc.).
4.  **Mildura Inclusion:** Mildura is no longer excluded and is correctly scraped (since it is in Victoria).
5.  **Melbourne/Bundoora Alias:** The scraper correctly maps 'Melbourne' mentions to the 'Bundoora' campus ID.
6.  **Gold Standard Test Case:** Bachelor of Accounting verifies exact ATARs:
    -   Melbourne (Bundoora): 61.90
    -   Bendigo: 60.25
    -   Online: 61.10
7.  **Complete Local Package:** Scraper saves both HTML and JSON snapshots for each course.
8.  **Passing Tests:** `test_migrate_latrobe.py` passes all tests (reproduction + live).

## Technical Constraints
-   Maintain `UniversalEngine` architecture.
-   Respect `robots.txt`.
-   Use existing `SiteConfig` for La Trobe (`f5b3d349-0214-480b-89bc-7b70298e722b`).

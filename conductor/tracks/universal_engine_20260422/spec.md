# Specification: Universal Scraper Engine & DB Migration

## Overview
Refactor the existing individual university scraping scripts into a centralized `UniversalEngine`. This engine will be driven by configurations stored in a new `site_configs` table, allowing for easier maintenance and scaling. It will also include a "Visual Anchor" fallback mechanism to improve resilience against website changes.

## Functional Requirements
1.  **Database Migration (`site_configs` table):**
    -   Create a new table to store extraction maps and metadata.
    -   Columns: `id` (PK), `university_id` (FK), `base_url`, `extraction_map` (jsonb), `robots_txt_status`, `version` (int), `is_active` (bool), `sample_urls` (text[]), `notes` (text), `last_updated` (timestamp).
    -   **Security:** Enable Row Level Security (RLS) on the `site_configs` table to restrict access. Define policies that allow the Service Role Key full access while restricting public/authenticated users based on project needs.
2.  **UniversalEngine (Python):**
    -   Single entry point for all scraping tasks.
    -   **Authentication:** Must use the Supabase **Service Role Key** for authentication, as it is a trusted backend process that needs to bypass RLS to manage configurations and results.
    -   Fetches the active configuration from `site_configs` based on `university_id`.
    -   Executes scraping logic using the `extraction_map` (CSS/XPath selectors).
    -   **Admissions Codes:** Implement extraction logic for admissions codes (e.g., VTAC codes for Victorian universities). The engine should be designed to handle generic `admissions_codes` mapping to accommodate other state-based admissions centers (UAC, QTAC, etc.) as the platform expands beyond Victoria.
3.  **Visual Anchor Logic:**
    -   Fallback mechanism when a primary CSS selector fails to find data.
    -   Searches the page for text anchors (labels) like "ATAR", "Fees", or "Duration" to locate associated data.
4.  **Confidence Scoring:**
    -   Assign a score to each extracted data point:
        -   **100:** Successful CSS match.
        -   **70:** Successful Text Anchor match.
        -   **30:** Fallback/Default value used.
    -   Store these scores in the database for auditing purposes.
5.  **Refactor & Cleanup:**
    -   Replace `unimelb.py`, `monash.py`, `rmit.py`, `swinburne.py`, and `latrobe.py` with configuration entries in `site_configs`.
    -   Ensure `UniversalEngine` handles all 5 Victorian universities.
6.  **La Trobe Validation:**
    -   Fix and properly validate the La Trobe scraping logic within the new engine context.

## Non-Functional Requirements
-   **Resilience:** Graceful handling of selector failures.
-   **Auditability:** Confidence scores must be logged to support annual data audits.
-   **Maintainability:** Centralized logic reduces code duplication.

## Acceptance Criteria
-   `site_configs` table exists and is populated with configs for the 5 Victorian universities.
-   `UniversalEngine` can successfully scrape data from all 5 universities.
-   Visual anchor logic successfully triggers and returns data when CSS selectors are intentionally broken in testing.
-   Confidence scores are correctly calculated and stored.
-   La Trobe scraper passes validation tests.

## Out of Scope
-   Managing `site_configs` via a web UI (to be handled in a separate track).
-   Migrating non-Victorian universities at this stage.

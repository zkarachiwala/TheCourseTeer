# Implementation Plan: Universal Scraper Engine

## Phase 1: Database Migration & Schema Setup [checkpoint: 3711428]
- [x] **Task: Create SQL migration for `site_configs`** [7a8c909]
    - [x] Create `db/migrations/20260422000001_create_site_configs.sql`
    - [x] Define columns: `id`, `university_id`, `base_url`, `extraction_map` (jsonb), `robots_txt_status`, `version`, `is_active`, `sample_urls`, `notes`, `last_updated`
    - [x] **Task: Enable RLS and define security policies**
        - [x] Add `ALTER TABLE site_configs ENABLE ROW LEVEL SECURITY;`
        - [x] Add policy to allow `service_role` full access
        - [x] Add policy to allow `authenticated` users read-only access (if applicable)
    - [x] Run migration and verify table structure in DB
- [x] **Task: Update Python models** [c573527]
    - [x] Add `SiteConfig` model to `scraper/models.py`
    - [x] Add `confidence_score` and `admissions_codes` fields to relevant result models
- [x] **Task: Seed initial configurations** [8045934]
    - [x] Create a seed script or migration to populate `site_configs` for UniMelb, Monash, RMIT, and Swinburne based on existing logic
    - [x] **Task: Map VTAC codes for Victorian universities**
        - [x] Research and extract VTAC codes from existing scripts or university pages
        - [x] Include VTAC selector logic in initial `extraction_map` seeds
- [x] **Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)**

## Phase 2: UniversalEngine Core Implementation [checkpoint: 4f96ac1]
- [x] **Task: Implement `UniversalEngine` Configuration Fetching** [4714d2b]
    - [x] **Task: Configure Supabase client with Service Role Key** [57d60e1]
        - [x] Update `.env` with `SUPABASE_SERVICE_ROLE_KEY`
        - [x] Ensure `scraper/db.py` uses this key for backend operations
    - [x] Write tests for fetching configs by `university_id`
    - [x] Implement `get_config` method in `UniversalEngine`
- [x] **Task: Implement Visual Anchor Logic** [1c6bcd8]
    - [x] Write tests for finding text anchors (e.g., "ATAR") in sample HTML
    - [x] Implement `find_by_anchor` method using BeautifulSoup or similar
- [x] **Task: Implement Generic Admissions Code Extraction** [a9dcf93]
    - [x] Write tests for extracting VTAC codes from sample Victorian pages
    - [x] Implement `extract_admissions_codes` method designed for extensibility (UAC, QTAC, etc.)
- [x] **Task: Implement Confidence Score Calculation** [4f96ac1]
    - [x] Write tests for score assignment (100 for CSS, 70 for Anchor, 30 for Fallback)
    - [x] Implement `calculate_confidence` logic
- [x] **Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)**

## Phase 3: Refactoring & Migration
- [x] **Task: Migrate UniMelb to UniversalEngine**
    - [x] Write integration test for UniMelb using `UniversalEngine`
    - [x] Ensure data parity with legacy script (including VTAC codes)
- [x] **Task: Migrate Monash to UniversalEngine**
    - [x] Write integration test for Monash
    - [x] Verify results, confidence scores, and VTAC codes
- [x] **Task: Migrate RMIT to UniversalEngine**
    - [x] Write integration test for RMIT
- [x] **Task: Migrate Swinburne to UniversalEngine**
    - [x] Write integration test for Swinburne
- [ ] **Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)**

## Phase 4: La Trobe Fix & Final Validation
- [ ] **Task: Fix and Validate La Trobe**
    - [ ] Identify and fix issues in La Trobe's extraction logic
    - [ ] Ensure VTAC codes are correctly mapped for La Trobe
    - [ ] Migrate to `UniversalEngine` and verify with integration tests
- [ ] **Task: Final Integration & Cleanup**
    - [ ] Run full test suite for all 5 Victorian universities
    - [ ] Delete legacy scripts (`unimelb.py`, `monash.py`, etc.) after confirmed parity
    - [ ] Update `scraper/run.py` to use `UniversalEngine` exclusively
- [ ] **Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)**

# Implementation Plan: Universal Scraper Engine

## Phase 1: Database Migration & Schema Setup
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
- [ ] **Task: Seed initial configurations**
    - [ ] Create a seed script or migration to populate `site_configs` for UniMelb, Monash, RMIT, and Swinburne based on existing logic
    - [ ] **Task: Map VTAC codes for Victorian universities**
... User modified the `new_string` content to be: # Implementation Plan: Universal Scraper Engine

## Phase 1: Database Migration & Schema Setup
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
- [ ] **Task: Seed initial configurations**
    - [ ] Create a seed script or migration to populate `site_configs` for UniMelb, Monash, RMIT, and Swinburne based on existing logic
    - [ ] **Task: Map VTAC codes for Victorian universities**
        - [ ] Research and extract VTAC codes from existing scripts or university pages
        - [ ] Include VTAC selector logic in initial `extraction_map` seeds
- [ ] **Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)**

## Phase 2: UniversalEngine Core Implementation
- [ ] **Task: Implement `UniversalEngine` Configuration Fetching**
    - [ ] **Task: Configure Supabase client with Service Role Key**
        - [ ] Update `.env` with `SUPABASE_SERVICE_ROLE_KEY`
        - [ ] Ensure `scraper/db.py` uses this key for backend operations
    - [ ] Write tests for fetching configs by `university_id`
    - [ ] Implement `get_config` method in `UniversalEngine`
- [ ] **Task: Implement Visual Anchor Logic**
    - [ ] Write tests for finding text anchors (e.g., "ATAR") in sample HTML
    - [ ] Implement `find_by_anchor` method using BeautifulSoup or similar
- [ ] **Task: Implement Generic Admissions Code Extraction**
    - [ ] Write tests for extracting VTAC codes from sample Victorian pages
    - [ ] Implement `extract_admissions_codes` method designed for extensibility (UAC, QTAC, etc.)
- [ ] **Task: Implement Confidence Score Calculation**
    - [ ] Write tests for score assignment (100 for CSS, 70 for Anchor, 30 for Fallback)
    - [ ] Implement `calculate_confidence` logic
- [ ] **Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)**

## Phase 3: Refactoring & Migration
- [ ] **Task: Migrate UniMelb to UniversalEngine**
    - [ ] Write integration test for UniMelb using `UniversalEngine`
    - [ ] Ensure data parity with legacy script (including VTAC codes)
- [ ] **Task: Migrate Monash to UniversalEngine**
    - [ ] Write integration test for Monash
    - [ ] Verify results, confidence scores, and VTAC codes
- [ ] **Task: Migrate RMIT to UniversalEngine**
    - [ ] Write integration test for RMIT
- [ ] **Task: Migrate Swinburne to UniversalEngine**
    - [ ] Write integration test for Swinburne
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

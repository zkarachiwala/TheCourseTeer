# Implementation Plan: Snapshot Caching System

## Phase 1: Infrastructure & Directory Setup
- [x] **Task: Update `.gitignore` and create snapshot root**
    - [x] Add `scraper/snapshots/` to `.gitignore`
    - [x] Create `scraper/snapshots/.gitkeep` (if we want the folder structure tracked, otherwise just ignore)
- [x] **Task: Create `scraper/snapshot_manager.py`**
    - [x] Implement `SnapshotManager` class.
    - [x] Implement URL hashing logic (SHA-256).
    - [x] Implement `get_snapshot_path(university_id, url)` logic.
    - [x] Implement `save(university_id, url, content)` and `load(university_id, url)` methods.

## Phase 2: BaseScraper Integration
- [x] **Task: Integrate caching into `BaseScraper`**
    - [x] Add `_use_cache` and `_force_refresh` properties to `BaseScraper`.
    - [x] Update `BaseScraper` to check cache in a unified way (if applicable).
- [x] **Task: Implement Cache TTL logic**
    - [x] Add `ttl_days` parameter to the manager.
    - [x] Check file modification time during `load()`.

## Phase 3: UniversalEngine & Auxiliary Support
- [x] **Task: Update `UniversalEngine.scrape_url`**
    - [x] Wrap the `make_client()` fetch in cache check/save.
- [x] **Task: Support auxiliary data snapshots**
    - [x] Ensure `follow_urls` fetches are also cached.
    - [x] Handle JSON vs HTML extensions correctly in filenames.

## Phase 4: CLI Control & Verification
- [ ] **Task: Add CLI flags to `run.py`**
    - [ ] Add `--no-cache` and `--refresh` flags.
- [ ] **Task: Final Verification**
    - [ ] Run a test scrape for 1 university and verify local files are created.
    - [ ] Run again and verify network is NOT hit (via logs).
    - [ ] Verify `--refresh` flag works.

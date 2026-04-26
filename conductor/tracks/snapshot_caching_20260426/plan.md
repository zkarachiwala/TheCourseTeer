# Implementation Plan: Snapshot Caching System

## Phase 1: Infrastructure & Directory Setup
- [ ] **Task: Update `.gitignore` and create snapshot root**
    - [ ] Add `scraper/snapshots/` to `.gitignore`
    - [ ] Create `scraper/snapshots/.gitkeep` (if we want the folder structure tracked, otherwise just ignore)
- [ ] **Task: Create `scraper/snapshot_manager.py`**
    - [ ] Implement `SnapshotManager` class.
    - [ ] Implement URL hashing logic (SHA-256).
    - [ ] Implement `get_snapshot_path(university_id, url)` logic.
    - [ ] Implement `save(university_id, url, content)` and `load(university_id, url)` methods.

## Phase 2: BaseScraper Integration
- [ ] **Task: Integrate caching into `BaseScraper`**
    - [ ] Add `_use_cache` and `_force_refresh` properties to `BaseScraper`.
    - [ ] Update `BaseScraper` to check cache in a unified way (if applicable).
- [ ] **Task: Implement Cache TTL logic**
    - [ ] Add `ttl_days` parameter to the manager.
    - [ ] Check file modification time during `load()`.

## Phase 3: UniversalEngine & Auxiliary Support
- [ ] **Task: Update `UniversalEngine.scrape_url`**
    - [ ] Wrap the `make_client()` fetch in cache check/save.
- [ ] **Task: Support auxiliary data snapshots**
    - [ ] Ensure `follow_urls` fetches are also cached.
    - [ ] Handle JSON vs HTML extensions correctly in filenames.

## Phase 4: CLI Control & Verification
- [ ] **Task: Add CLI flags to `run.py`**
    - [ ] Add `--no-cache` and `--refresh` flags.
- [ ] **Task: Final Verification**
    - [ ] Run a test scrape for 1 university and verify local files are created.
    - [ ] Run again and verify network is NOT hit (via logs).
    - [ ] Verify `--refresh` flag works.

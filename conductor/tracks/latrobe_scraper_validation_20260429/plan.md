# La Trobe Scraper Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve missing VTAC codes, restore reproduction samples, include Mildura, support Melbourne/Bundoora alias, and verify Bachelor of Accounting gold-standard ATARs.

**Architecture:** Use `UniversalEngine` with enhanced JSON/HTML extraction. Restore missing local samples to enable stable TDD.

**Tech Stack:** Python, BeautifulSoup, httpx, pytest, UniversalEngine.

---

### Task 1: Restore Reproduction Samples & Gold-Standard Test

**Files:**
- Create: `scraper/latrobe_sample.html` (Bachelor of Arts)
- Create: `scraper/latrobe_detail_sample.json` (Bachelor of Arts)
- Create: `scraper/latrobe_accounting_sample.html` (Bachelor of Accounting)
- Create: `scraper/latrobe_accounting_detail.json` (Bachelor of Accounting)
- Modify: `scraper/tests/test_migrate_latrobe.py`

- [x] 
 **Step 1: Fetch fresh samples from La Trobe (Arts & Accounting)**
  Run: `cd scraper && uv run python -c "import httpx; r = httpx.get('https://www.latrobe.edu.au/courses/bachelor-of-arts'); open('latrobe_sample.html', 'w').write(r.text); r2 = httpx.get('https://www.latrobe.edu.au/courses/data/2026/domestic/vic/bachelor-of-arts?v=1.0'); open('latrobe_detail_sample.json', 'w').write(r2.text); ra = httpx.get('https://www.latrobe.edu.au/courses/bachelor-of-accounting'); open('latrobe_accounting_sample.html', 'w').write(ra.text); ra2 = httpx.get('https://www.latrobe.edu.au/courses/data/2026/domestic/vic/bachelor-of-accounting?v=1.0'); open('latrobe_accounting_detail.json', 'w').write(ra2.text)"`

- [x] 
 **Step 2: Add Gold-Standard Test for Bachelor of Accounting**
  Add `test_latrobe_accounting_gold_standard` to `scraper/tests/test_migrate_latrobe.py` with the following assertions:
  - Melbourne (Bundoora): 61.90
  - Bendigo: 60.25
  - Online: 61.10

- [x] 
 **Step 3: Run new test to verify it fails (Red)**
  Run: `cd scraper && uv run pytest tests/test_migrate_latrobe.py::test_latrobe_accounting_gold_standard`

- [x] 
 **Step 4: Commit samples and failing test**
  Run: `git add scraper/latrobe_*.html scraper/latrobe_*.json scraper/tests/test_migrate_latrobe.py && git commit -m "test: add La Trobe gold-standard accounting test and samples"`

---

### Task 2: Update Configuration (Mildura & Melbourne Alias)

**Files:**
- Modify: `scraper/seed_site_configs.py`
- Modify: `scraper/universal_engine.py`

- [x] 
 **Step 1: Add 'Melbourne' -> 'Bundoora' mapping**
  Update `LATROBE_CAMPUS_CODES` or the `SiteConfig` in `scraper/seed_site_configs.py` to include `"Melbourne": "Bundoora"`.

- [x] 
 **Step 2: Ensure Mildura is not filtered out**
  Verify `universal_engine.py` or `seed_site_configs.py` doesn't have a hardcoded filter for Mildura.

- [x] 
 **Step 3: Update SiteConfig to handle HTML-based VTAC fallback**
  Modify `scraper/seed_site_configs.py` to add a selector for VTAC codes if JSON fails.
  ```python
  "admissions_codes": {
      "selector": ".ds-course-header__vtac-code", 
      "regex": r"(\d{10})"
  }
  ```

- [x] 
 **Step 4: Run seed script to update DB**
  Run: `cd scraper && uv run python seed_site_configs.py`

- [x] 
 **Step 5: Commit**
  Run: `git add scraper/seed_site_configs.py && git commit -m "fix(latrobe): add Melbourne alias and VTAC fallback"`

---

### Task 3: Fix Campus-ATAR Mapping Logic

**Files:**
- Modify: `scraper/universal_engine.py`
- Test: `scraper/tests/test_migrate_latrobe.py`

- [x] 
 **Step 1: Enhance `UniversalEngine` to handle precise ATAR floats**
  Ensure it extracts `61.90` not just `61`.

- [x] 
 **Step 2: Fix any mapping logic in `universal_engine.py`**
  Ensure `atar_json_map` correctly identifies campus codes and aliases.

- [x] 
 **Step 3: Verify with gold-standard test (Green)**
  Run: `cd scraper && uv run pytest tests/test_migrate_latrobe.py::test_latrobe_accounting_gold_standard`

- [x] 
 **Step 4: Verify with live integration test**
  Run: `cd scraper && uv run pytest tests/test_migrate_latrobe.py::test_latrobe_live_integration -s`

- [x] 
 **Step 5: Commit**
  Run: `git add scraper/universal_engine.py && git commit -m "fix(latrobe): improve campus-atar mapping and precision"`

---

### Task 4: Final Documentation & Track Cleanup

- [x] 
 **Step 1: Update `conductor/tracks.md`**
  Mark the track as complete once all tasks are done.
  
- [x] 
 **Step 2: Commit documentation**
  Run: `git add conductor/tracks.md && git commit -m "docs: complete La Trobe validation track"`

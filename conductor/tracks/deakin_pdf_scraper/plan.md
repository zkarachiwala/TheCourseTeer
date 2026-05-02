# Deakin University PDF Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape undergraduate courses and ATAR scores for Deakin University using their official Undergraduate Course Guide PDF, bypassing the Cloudflare bot protection on their website.

**Architecture:** A standalone Python script (`scraper/deakin_pdf_parser.py`) will read the downloaded `deakin_guide.pdf` using a PDF parsing library (like `pypdf` or `pdfplumber`). It will extract course titles, campus availability, Selection Rank (ATAR), and Guaranteed ATAR. It will then use the existing database functions to upsert the courses and campus links.

**Tech Stack:** Python, `pypdf` (or similar), PostgreSQL (via existing `db.py`)

---

### Task 1: Setup PDF Parsing Script

**Files:**
- Create: `scraper/deakin_pdf_parser.py`

- [ ] **Step 1: Install PDF library**
  Run: `uv add pypdf` (or `pdfplumber` if preferred for table extraction)
  Expected: Library installed successfully.

- [ ] **Step 2: Create parser script skeleton**
  Write the initial structure for `scraper/deakin_pdf_parser.py` that opens `deakin_guide.pdf` and extracts text page by page.
  Expected: Script runs and prints raw text from a sample page (e.g., page 16) to verify extraction quality.

### Task 2: Implement Data Extraction Logic

**Files:**
- Modify: `scraper/deakin_pdf_parser.py`

- [ ] **Step 1: Define campus mapping**
  Map the PDF abbreviations to Deakin's campus IDs:
  - `B`: Melbourne Burwood
  - `WP`: Geelong Waurn Ponds
  - `WF`: Geelong Waterfront
  - `WB`: Warrnambool
  - `O`: Online

- [ ] **Step 2: Extract course blocks**
  Write regex or string matching logic to identify course names (starting with "Bachelor of"), their associated campuses, and the "ATAR" and "GUARANTEED ATAR" values from the text.
  Expected: Script successfully prints a list of parsed course dictionaries with names, campuses, and scores.

### Task 3: Database Integration

**Files:**
- Modify: `scraper/deakin_pdf_parser.py`

- [ ] **Step 1: Connect to DB and upsert**
  Import `get_pool`, `upsert_course`, and `upsert_campus_link` from `scraper.db`.
  Iterate through the parsed courses and save them to the database under Deakin's university ID (`f4845481-ddf4-4941-973e-5c1a617b7677`).

- [ ] **Step 2: Log missing ATARs**
  Import `record_atar_issue`. If a course has 'NP', 'NA', or blank ATARs, log it to the `atar_issues` table.
  Expected: Script runs completely, inserting courses into the database.

### Task 4: Verification

**Files:**
- N/A

- [ ] **Step 1: Verify data in DB**
  Run: `psql $DATABASE_URL -c "SELECT c.name, cam.name, cc.atar_lowest_selection_rank FROM courses c JOIN course_campuses cc ON c.id = cc.course_id JOIN campuses cam ON cc.campus_id = cam.id WHERE c.university_id = 'f4845481-ddf4-4941-973e-5c1a617b7677' LIMIT 10;"`
  Expected: Deakin courses and their ATARs are populated correctly.

# Data Conventions

## ATAR Fields

Two distinct ATAR fields exist on `course_campuses`. They must never be conflated:

| Field | Meaning | Notes |
|---|---|---|
| `atar_guaranteed` | Guaranteed entry ATAR (marketing threshold) | If you meet this score, entry is guaranteed |
| `atar_lowest_selection_rank` | Lowest actual selection rank from the previous intake | Reflects real competition; more accurate for comparison |

Both are **nullable integers**. Many universities publish only one. Store `NULL`, never `0`, when a value is absent or not published (`NP`, `NA`, blank).

---

## `extraction_notes` Convention

`course_campuses.extraction_notes` documents scraper fallback behaviour.

- **Populate it** whenever data was inferred or read from a fallback source (e.g. ATAR read from a global course page rather than a campus-specific section).
- **Leave it `NULL`** when extraction matched the expected template exactly. `NULL` means clean extraction.

This field is the audit trail for data quality. It powers the admin health dashboard's fallback reporting.

---

## Undergraduate-Only Filter

The database must only contain undergraduate courses. Any course identified as postgraduate must be discarded **before** the upsert phase.

Discard if any of the following are true:
- `degree_type` is `PG`
- Course name contains: `Masters`, `Doctor`, `Graduate Diploma`, `Graduate Certificate`
- `courseLevelCode` maps to a postgraduate level

---

## robots.txt Compliance

**This is a first-class legal requirement, not optional.**

- The scraper checks `robots.txt` before crawling any university.
- Parsed allow/disallow rules are stored in `universities.robots_txt_rules` (jsonb).
- If scraping is disallowed for a path, that university is **skipped** and the status is logged as `robots_blocked` in `universities.scraper_status`.

---

## Pricing Fields

| Field | Meaning |
|---|---|
| `price_annual_csp_aud` | Annual student contribution for CSP (Commonwealth Supported) places. `NULL` if no CSP places offered. |
| `price_annual_dfee_aud` | Annual full-fee domestic rate. `NULL` if not offered. |

Prices are stored as integers (whole AUD). Domestic pricing only in Phase 1.

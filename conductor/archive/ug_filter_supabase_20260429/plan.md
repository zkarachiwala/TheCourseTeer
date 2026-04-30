# Implementation Plan: Undergraduate Filter & Supabase Configuration

## Context
**Objective:** Ensure only undergraduate courses are processed by default and strictly enforce the use of Supabase for the database connection in both code and documentation.
**Spec:** `conductor/tracks/ug_filter_supabase_20260429/spec.md`

## 1. Documentation & Database Configuration Updates

### 1.1 `.env.example`
- Replace the local Docker `DATABASE_URL` with a Supabase placeholder URL (`postgresql://postgres.[project_ref]:[password]@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require`).
- Add a new environment variable: `COURSE_LEVEL_FILTER=UG` with a comment explaining its purpose.

### 1.2 `web/.env.local.example`
- If it exists, update `DATABASE_URL` to match `.env.example`'s Supabase connection string.
- Add `COURSE_LEVEL_FILTER=UG` if relevant to the web app (though mainly for the scraper).

### 1.3 `README.md`
- Search and replace "undergraduate and postgraduate" with "undergraduate".
- Update the "Database" or "Getting Started" section to explicitly direct the user to use the Supabase database. State that local development must point to the Supabase instance using `sslmode=require`.

## 2. Configurable Course Filter Implementation

### 2.1 `scraper/universal_engine.py`
- Modify `_is_valid_course(self, name: str, url: str) -> bool` to:
  - Read `os.getenv("COURSE_LEVEL_FILTER", "UG")`.
  - If the filter is `UG`, identify postgraduate keywords ("master", "doctor", "juris doctor", "graduate certificate", "graduate diploma") in the course name.
  - Return `False` if the course contains postgraduate keywords.

### 2.2 `scraper/ai_parse.py`
- Update the `prompt` definition (around where it lists field extraction rules) to explicitly state:
  - "If `COURSE_LEVEL_FILTER=UG` (or if you are unsure), extract ONLY undergraduate courses."
  - Modify the rule for `degree_type` to say "- For 'degree_type', return ONLY 'UG' (unless 'PG' is explicitly enabled via config)."

## 3. Testing & Validation
- Run unit tests (`pytest scraper/tests/test_universal_engine.py`) and update any assertions that test PG courses if the filter now universally blocks them (or conditionally test them based on the new environment variable).
- Verify the new `_is_valid_course` logic works against typical PG course names.
- Ensure the codebase builds correctly with the new config values.
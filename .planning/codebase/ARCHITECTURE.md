<!-- refreshed: 2025-05-15 -->
# Architecture

**Analysis Date:** 2025-05-15

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
├──────────────────┬──────────────────┬───────────────────────┤
│   Course Search  │   Admin Dashboard│   Scraper Builder     │
│  `web/src/app`   │ `web/src/app/admin`│`web/src/app/admin/sb` │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    API & Business Logic                      │
│         `web/src/api` & `web/src/lib`                        │
└─────────────────────────────────────────────────────────────┘
         │                  │
         │                  ▼
         │      ┌──────────────────────────┐
         │      │ Python Scraper Engine    │
         │      │ `scraper/universal_engine.py`
         │      └───────────┬──────────────┘
         │                  │
         ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Database (PostgreSQL / Supabase)                            │
│  `web/db/schema.ts` & `db/migrations`                        │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Frontend** | React-based user interface for browsing courses and admin tasks. | `web/src/app` |
| **API Layer** | Server-side actions and API routes for data fetching and proxying. | `web/src/app/api` |
| **Universal Engine** | Centralized Python scraper driven by database configurations. | `scraper/universal_engine.py` |
| **Scraper Builder** | Visual tool for identifying data points on university sites. | `web/src/app/admin/scraper-builder` |
| **ORM / Schema** | Database definitions and object-relational mapping using Drizzle. | `web/db/schema.ts` |
| **Snapshot Manager** | Handles local caching of scraped HTML/JSON for debugging and speed. | `scraper/snapshot_manager.py` |

## Pattern Overview

**Overall:** Decoupled Frontend/Backend with Configuration-Driven Scraper.

**Key Characteristics:**
- **Full-stack Next.js:** React for UI, Server Components/Actions for backend logic.
- **Config-Driven Scraping:** Scraper behavior is controlled by JSON maps in the database, not hardcoded scripts.
- **Hybrid Fetching:** Supports both static HTTP requests and browser-based scraping (Playwright) for SPA-like sites.

## Layers

**UI Layer:**
- Purpose: Presentation and user interaction.
- Location: `web/src/app`
- Contains: React components, Tailwind styles, and Client-side state.
- Depends on: API Layer (via Server Actions).

**Scraping Layer:**
- Purpose: Automated data extraction from university websites.
- Location: `scraper/`
- Contains: Python scripts, extraction logic, and local snapshots.
- Depends on: Database (for config and storage), Playwright (for browser automation).

**Data Layer:**
- Purpose: Persistent storage for courses, university metadata, and scraper configurations.
- Location: `web/db` and `db/migrations`
- Contains: SQL migrations, Drizzle schema definitions.
- Used by: Both the Next.js API and the Python Scraper.

## Data Flow

### Primary Request Path (User Search)

1. **Entry:** User visits `/courses` or searches for a course. (`web/src/app/courses/page.tsx`)
2. **Processing:** Server Component fetches data from PostgreSQL via Drizzle. (`web/db/schema.ts`)
3. **Response:** Paginated list of courses is rendered and returned to the client.

### Scraping Flow

1. **Trigger:** `scraper/run.py` is invoked (manually or via CI/CD).
2. **Config:** `UniversalEngine` fetches `site_configs` from the database. (`scraper/db.py`)
3. **Discovery:** Scraper finds course URLs via sitemaps or listing pages. (`scraper/universal_engine.py`)
4. **Extraction:** Scraper fetches page (HTML/JSON) and applies extraction map.
5. **Storage:** Extracted `CourseData` is upserted into the database. (`scraper/db.py`)

## Key Abstractions

**`BaseScraper`:**
- Purpose: Abstract base class for all scraper implementations.
- Examples: `scraper/base_scraper.py`
- Pattern: Template Method.

**`SiteConfig`:**
- Purpose: JSON-based extraction map defining how to find fields (name, ATAR, etc.) on a page.
- Examples: `scraper/models.py`, `db/migrations/20260422000001_create_site_configs.sql`
- Pattern: Configuration Object.

## Entry Points

**Web App:**
- Location: `web/src/app/page.tsx`
- Triggers: Browser request to root URL.
- Responsibilities: Main landing page and entry to course search.

**Scraper Runner:**
- Location: `scraper/run.py`
- Triggers: CLI command `uv run python run.py`.
- Responsibilities: Orchestrates scraping runs for multiple universities.

## Architectural Constraints

- **PostgreSQL/Supabase:** All persistent data must reside in the central Postgres database.
- **Python for Scraping:** Heavy lifting for extraction and browser automation is restricted to the Python `scraper/` module.
- **Next.js for Frontend:** The web interface must be built with Next.js using the App Router.
- **UTC Timestamps:** All database timestamps must be stored and compared in UTC.

## Anti-Patterns

### Hardcoded Selectors

**What happens:** Writing specific scraping scripts for every university.
**Why it's wrong:** High maintenance overhead as university sites change frequently.
**Do this instead:** Add an entry to `site_configs` and use `UniversalEngine`.

### Duplicate Course Entries

**What happens:** Multiple rows for the same course from the same university.
**Why it's wrong:** Degrades search quality and user experience.
**Do this instead:** Use `ON CONFLICT (university_id, source_url)` in `upsert_course` in `scraper/db.py`.

## Error Handling

**Strategy:** Fail-safe scraping with issue logging.

**Patterns:**
- **ATAR Issues:** Failed ATAR extractions are logged to the `atar_issues` table for manual review. (`scraper/db.py:log_atar_issue`)
- **Scraper Status:** University status is tracked (e.g., `last_ok`, `failing`, `robots_blocked`) in the `universities` table.

## Cross-Cutting Concerns

**Logging:** Standard Python `logging` in the scraper; console logging in the web app.
**Validation:** Zod schemas (implicitly via Drizzle/Typescript) in the web app; `models.py` (Pydantic-like dataclasses) in the scraper.
**Authentication:** Next.js Auth Context (`web/src/contexts/auth-context.tsx`) and Supabase RLS.

---

*Architecture analysis: 2025-05-15*

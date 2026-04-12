# Technical Specification: Australian University Course Aggregator

> **Living document.** When any requirement, decision, or scope item is clarified or changed, this file must be updated immediately to reflect the current agreed state. The PLAN_REVIEW.md file records the rationale for decisions made.

## 1. Project Overview
This project creates a comprehensive, persistent data repository and a responsive web application that aggregates undergraduate and postgraduate course information from all Australian-based universities. The core value proposition is an AI-driven data extraction engine that adapts to website changes and provides a unified search experience for students.

## 2. Data Acquisition Strategy (The Engine)
The system employs a hybrid approach to data collection, prioritizing efficiency and resilience.

### 2.1 Discovery & API Integration
- **API First:** The engine will first check for publicly available APIs or structured data feeds (JSON/LD, Schema.org metadata).
- **Government Databases:** Cross-reference with CRICOS (Commonwealth Register of Institutions and Courses for Overseas Students) or the Department of Education datasets where applicable.

### 2.2 AI-Adaptive Scraping (The "Self-Healing" Scraper)
- **Technology:** Playwright (Python). Not Puppeteer.
- **LLM:** Local/open-source model preferred to minimize cost (investigate Ollama + Mistral/Llama 3 as first option). Fallback: Claude Haiku (`claude-haiku-4-5-20251001`). BERT/fine-tuned models dropped — no training data available.
- **Re-mapping trigger:** Exception-based (Option A). If a selector throws an exception, immediately trigger an AI re-mapping attempt. The failing selector and its AI-generated replacement are stored in `scraper_configs` for auditability.
- **Config storage:** Selectors and extraction rules are stored in a `scraper_configs` table in Postgres: `(university_id, field_name, selector, last_verified_at, ai_generated: bool)`.
- **robots.txt compliance:** The scraper checks `robots.txt` before crawling any university. Parsed rules are stored in the `universities` table. If scraping is disallowed for a path, that university is skipped and the status is logged. This is a first-class legal requirement.
- **Per-university scraper config:** Each university has a documented scraper mode (`static` or `browser`), URL pattern, and data field locations. See [UNIVERSITIES.md](UNIVERSITIES.md).
- **Periodic Scheduling:** Cron job on the worker host. Monthly runs to capture handbook updates. No separate scheduler service for MVP.

## 3. Data Schema & Storage

### 3.1 Infrastructure
- **Local dev:** Docker Compose with Postgres.
- **Production:** Supabase (managed Postgres, free tier for MVP). Migrate to RDS if scale demands it.
- **Scraper worker:** Long-running Python process on a VPS or Railway worker. Not serverless (Playwright requires a real browser).

### 3.2 Universities Table
A `universities` table is required. University is not just a field on `courses`.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| name | text | Official name |
| slug | text | URL-safe identifier |
| homepage_url | text | |
| scraper_status | text | last_ok, failing, robots_blocked, etc. |
| robots_txt_rules | jsonb | Parsed allow/disallow rules |
| last_scraped_at | timestamptz | |

### 3.3 Courses Table

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| university_id | uuid | FK -> universities |
| name | text | |
| faculty | text | |
| campus | text | |
| degree_type | text | UG or PG |
| duration_years | numeric | Standard duration |
| source_url | text | Direct link to course page |
| price_annual_csp_aud | integer | Student contribution (annual). Null if no CSP places. |
| price_annual_dfee_aud | integer | Full-fee domestic (annual). Null if not offered. |
| csp_available | boolean | |
| atar_guaranteed | integer | Guaranteed entry ATAR. Nullable. |
| atar_lowest_selection_rank | integer | Actual lowest rank offered. Nullable. |
| prerequisites | jsonb | Array of strings e.g. `["English (any)", "Maths Methods"]` |
| updated_at | timestamptz | |
| created_at | timestamptz | |

### 3.4 Course Prerequisites Table (UG -> PG pathways)
Created at schema setup even if empty in MVP.

| Field | Type | Notes |
|---|---|---|
| course_id | uuid | FK -> courses (the Masters course) |
| requires_course_id | uuid | FK -> courses (the UG course) |
| notes | text | Nullable. E.g. "minimum credit average required." |

### 3.5 Scraper Configs Table

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| university_id | uuid | FK -> universities |
| field_name | text | e.g. "atar_guaranteed" |
| selector | text | CSS/XPath selector |
| last_verified_at | timestamptz | |
| ai_generated | boolean | True if set by AI re-mapping |

## 4. Web Application Architecture

### 4.1 Frontend Tech Stack
- **Framework:** Next.js (App Router, v14+). Server Components query the database directly for read operations — no separate API layer needed for the UI.
- **Styling:** Tailwind CSS.
- **Theming:** `next-themes` for System/Dark/Light mode.

### 4.2 Backend / Scraper Management
- **Scraper:** Python service (Playwright + FastAPI). FastAPI exposes scraper management endpoints (trigger run, view status, view logs).
- **Read path:** Next.js Server Components -> Postgres (via ORM, e.g. Drizzle or Prisma).
- **Write path:** Python scraper -> Postgres directly.

### 4.3 Key Features
- **Search & Filter:** Multi-select filters for Faculty, Campus, Degree Type, and ATAR ranges.
- **Full-text search:** Postgres `tsvector`. No Elasticsearch/Algolia unless proven necessary.
- **Responsive Layout:** Mobile-first design.
- **External Launch:** All course links target `_blank`.

## 5. Implementation Roadmap

### Phase 1: MVP
- Database schema setup (all tables including `course_prerequisites` and `scraper_configs`).
- Scraper for 5 MVP universities: University of Melbourne, University of Sydney, RMIT, Monash University, University of Queensland.
- Per-university scraping approach, URL patterns, and data availability: see [UNIVERSITIES.md](UNIVERSITIES.md).
- robots.txt compliance built in from the start.
- Basic search interface with Dark/Light/System mode.
- Domestic pricing only.

### Phase 2: Scaling
- Expand scraper coverage to all 40+ Australian universities (see [UNIVERSITIES.md](UNIVERSITIES.md) for full list and status).
- Implement full AI re-mapping logic with `scraper_configs` audit trail.
- Prerequisite Mapping for Masters courses (populate `course_prerequisites`).
- Normalise prerequisite subjects if significant variation found across universities.

### Phase 3: Future Enhancements
- **User Profiles:** Save Search, Shortlist courses.
- **Authentication:** OAuth (Google/Apple/LinkedIn).
- **International Pricing:** Multi-currency, international student requirements.

## 6. Technical Maintenance
- **Health Dashboard:** Internal URL (no auth for MVP). Shows scraper status per university, last run time, failing selectors, and robots_blocked entries.
- **Data versioning:** `updated_at` timestamp per row for MVP. Full `course_history` audit table in Phase 2.

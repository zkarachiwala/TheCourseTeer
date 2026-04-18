# Technical Specification: Australian University Course Aggregator

> **Living document.** When any requirement, decision, or scope item is clarified or changed, this file must be updated immediately to reflect the current agreed state. The PLAN_REVIEW.md file records the rationale for decisions made.

## 0. Development Process

All feature work and changes to this codebase must follow the `/feature-dev` 7-phase workflow:

1. **Discovery** — Understand what needs to be built. Confirm scope with the user.
2. **Codebase Exploration** — Read and understand relevant existing code before writing anything.
3. **Clarifying Questions** — Surface all ambiguities and edge cases. Wait for answers before designing.
4. **Architecture Design** — Present multiple approaches with trade-offs. Get explicit user approval.
5. **Implementation** — Build only after approval. Follow existing conventions strictly.
6. **Quality Review** — Review for simplicity, correctness, and consistency with the codebase.
7. **Summary** — Document what was built, decisions made, and suggested next steps.

Invoke with `/feature-dev:feature-dev [description of change]` at the start of any new feature, bugfix, or non-trivial modification. Do not skip phases or proceed past Phase 4 without explicit user approval.

## 1. Project Overview
This project creates a comprehensive, persistent data repository and a responsive web application that aggregates undergraduate and postgraduate course information from all Australian-based universities. The core value proposition is an AI-driven data extraction engine that adapts to website changes and provides a unified search experience for students.

## 2. Data Acquisition Strategy (The Engine)
The system employs a hybrid approach to data collection, prioritizing efficiency and resilience.

### 2.1 Discovery & API Integration
- **API First:** The engine will first check for publicly available APIs or structured data feeds (JSON/LD, Schema.org metadata).
- **Government Databases:** Cross-reference with CRICOS (Commonwealth Register of Institutions and Courses for Overseas Students) or the Department of Education datasets where applicable.

### 2.3 Scraper Execution Options

The scraper is decoupled from app hosting. It runs independently and writes directly to Supabase. FastAPI scraper management endpoints are not required — trigger, logs, and status are handled as described below.

Given the expected run frequency (annually for handbook updates), options ranked by preference:

| Option | Cost | Trigger | Logs | Notes |
|---|---|---|---|---|
| **GitHub Actions** (recommended) | Free (public repo) / 2,000 min/month free (private) | Manual (`workflow_dispatch`) or cron schedule | Actions run log | No infrastructure to maintain. Playwright installs cleanly on Ubuntu runners. |
| **Local machine** | Free | Manual | Terminal | Simplest for infrequent runs. No cloud dependency. |
| **Azure Container Apps** (consumption plan) | Free allowance: 180k vCPU-sec/month | Azure scheduler or manual | Container log stream | Use if automation or team access is needed without GitHub Actions. |

For all options, scraper status is visible in the Next.js health dashboard via the `scraper_status` and `last_scraped_at` columns in the `universities` table.

**LLM note:** GitHub Actions and Azure Container Apps have no local Ollama available. Selector re-mapping failures fall through to Claude Haiku (API cost is negligible for infrequent runs). Running locally keeps Ollama available.

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
- **Local dev:** Docker Compose with Postgres 17 + Adminer (web DB browser on port 8080).
- **Migrations:** dbmate. Plain SQL files in `db/migrations/`. Run with `scripts/migrate.bat` (Windows) or `bash scripts/migrate.sh`.
- **Production database:** Supabase (managed Postgres, free tier for MVP). Migrate to RDS if scale demands it.
- **App hosting:** Azure Static Web Apps (free tier). Next.js App Router with hybrid SSR via built-in serverless runtime.
- **Scraper:** Decoupled from app hosting. Runs independently on demand. See Section 2.3 for execution options.

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

### 3.3 Campuses Table

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| university_id | uuid | FK -> universities ON DELETE CASCADE |
| name | text | e.g. "City Campus", "Clayton" |
| slug | text | URL-safe identifier |
| address | text | Full street address |
| latitude | numeric | For map display (mapping service integration deferred) |
| longitude | numeric | For map display (mapping service integration deferred) |
| is_online | boolean | True for virtual/online campuses |

### 3.4 Courses Table

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| university_id | uuid | FK -> universities |
| name | text | |
| faculty | text | |
| degree_type | text | UG or PG |
| duration_years | numeric | Standard duration |
| source_url | text | Direct link to course page |
| price_annual_csp_aud | integer | Student contribution (annual). Null if no CSP places. |
| price_annual_dfee_aud | integer | Full-fee domestic (annual). Null if not offered. |
| csp_available | boolean | |
| prerequisites | jsonb | Array of strings e.g. `["English (any)", "Maths Methods"]` |
| updated_at | timestamptz | |
| created_at | timestamptz | |

### 3.4a Course Campuses Table

A course may be offered at multiple campuses. ATAR requirements can differ per campus.

| Field | Type | Notes |
|---|---|---|
| course_id | uuid | FK -> courses ON DELETE CASCADE |
| campus_id | uuid | FK -> campuses ON DELETE CASCADE |
| atar_guaranteed | integer | Guaranteed entry ATAR for this campus. Nullable. |
| atar_lowest_selection_rank | integer | Lowest selection rank for this campus. Nullable. |
| extraction_notes | text | Nullable. Populated only when a fallback was used during scraping (e.g. ATAR read from global page rather than a campus-specific section). NULL means extraction was clean. |

Primary key: `(course_id, campus_id)`.

**Scraper convention:** All university scrapers must populate `extraction_notes` on a `CampusLink` whenever data is inferred or read from a fallback source rather than the expected location. Leave it `None` when extraction matched the expected template exactly.

### 3.5 Course Prerequisites Table (UG -> PG pathways)
Created at schema setup even if empty in MVP.

| Field | Type | Notes |
|---|---|---|
| course_id | uuid | FK -> courses (the Masters course) |
| requires_course_id | uuid | FK -> courses (the UG course) |
| notes | text | Nullable. E.g. "minimum credit average required." |

### 3.6 Scraper Configs Table

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
- **Scraper:** Standalone Python service (Playwright). Runs independently of the app — no FastAPI layer required. See Section 2.3 for execution options.
- **Read path:** Next.js Server Components -> Supabase Postgres (via ORM, e.g. Drizzle or Prisma).
- **Write path:** Python scraper -> Supabase Postgres directly.

### 4.3 Key Features
- **Search & Filter:** Multi-select filters for Faculty, Campus, Degree Type, and ATAR ranges.
- **Full-text search:** Postgres `tsvector`. No Elasticsearch/Algolia unless proven necessary.
- **Responsive Layout:** Mobile-first design.
- **External Launch:** All course links target `_blank`.

## 5. Implementation Roadmap

### Phase 1: MVP
- Database schema setup (all tables including `course_prerequisites` and `scraper_configs`).
- Scraper for Victorian universities: RMIT, Monash University, University of Melbourne, La Trobe, Deakin, Federation University, Swinburne, Victoria University.
- Multi-campus model: courses link to campuses via `course_campuses` join table; ATAR stored per campus.
- One "Online" campus per university (flagged `is_online = true`).
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

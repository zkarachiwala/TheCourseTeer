# Codebase Structure

**Analysis Date:** 2025-05-15

## Directory Layout

```
[project-root]/
├── .claude/            # Claude-specific configurations and skills
├── conductor/          # Project management, tracks, and guidelines
├── db/                 # Database migrations (SQL)
│   └── migrations/     # Raw SQL migration files
├── planning/           # High-level project plans and research docs
├── scraper/            # Python-based scraping engine
│   ├── snapshots/      # Cached HTML/JSON from scraped sites
│   └── tests/          # Scraper unit and integration tests
├── scripts/            # Miscellaneous utility scripts (migration, etc.)
└── web/                # Next.js web application
    ├── db/             # Drizzle ORM schema and migrations
    ├── public/         # Static assets for the web app
    └── src/            # Application source code
        ├── app/        # Next.js App Router pages and API
        ├── components/ # Reusable React components
        ├── contexts/   # React Context providers (Auth, Shortlist)
        └── lib/        # Shared utility functions
```

## Directory Purposes

**`web/src/app`:**
- Purpose: Primary application logic and routing.
- Contains: Page components, layout definitions, and API routes.
- Key files: `page.tsx`, `layout.tsx`, `api/proxy/route.ts`.

**`scraper/`:**
- Purpose: The core data ingestion engine.
- Contains: Scraper logic, database interaction for scraping, and configuration management.
- Key files: `universal_engine.py`, `base_scraper.py`, `run.py`.

**`db/migrations`:**
- Purpose: Source of truth for database schema.
- Contains: SQL files that define tables, indexes, and policies.
- Key files: `20260422000001_create_site_configs.sql`, `20260414000002_create_courses.sql`.

**`conductor/`:**
- Purpose: Active project tracking and guidelines.
- Contains: Markdown files for product definition, tech stack, and workflow.
- Key files: `product.md`, `tech-stack.md`, `tracks.md`.

## Key File Locations

**Entry Points:**
- `web/src/app/page.tsx`: Web application home page.
- `scraper/run.py`: Main entry for running scrapers.
- `scraper/seed_site_configs.py`: Script to seed/update scraper configurations.

**Configuration:**
- `web/package.json`: Frontend dependencies and scripts.
- `scraper/pyproject.toml`: Python dependencies managed by `uv`.
- `web/drizzle.config.ts`: Database ORM configuration.

**Core Logic:**
- `scraper/universal_engine.py`: Centralized scraping logic.
- `web/src/app/admin/scraper-builder/actions.ts`: Server actions for the visual scraper builder.

**Testing:**
- `scraper/tests/`: Python test suite for the scraper.
- `web/src/__tests__/`: Frontend test suite.

## Naming Conventions

**Files:**
- TypeScript/React: kebab-case for files, PascalCase for components (e.g., `course-card.tsx`).
- Python: snake_case (e.g., `base_scraper.py`).
- SQL: YYYYMMDDHHMMSS_description.sql (e.g., `20260414000001_create_universities.sql`).

**Directories:**
- General: kebab-case (e.g., `scraper-builder`).

## Where to Add New Code

**New Feature (Web):**
- Primary code: `web/src/app/[feature]/page.tsx`
- Components: `web/src/components/[feature]/`
- Tests: `web/src/__tests__/[feature].test.ts`

**New University Scraper:**
- Implementation: Add configuration to `scraper/seed_site_configs.py`.
- Universal Engine adjustment (if needed): `scraper/universal_engine.py`.

**Utilities:**
- Shared helpers (Web): `web/src/lib/`
- Shared helpers (Scraper): `scraper/`

## Special Directories

**`scraper/snapshots/`:**
- Purpose: Stores local copies of fetched HTML and JSON for development and debugging.
- Generated: Yes (during scraper runs).
- Committed: No (ignored by `.gitignore`).

**`conductor/archive/`:**
- Purpose: Record of completed project tracks and historical decisions.
- Generated: No.
- Committed: Yes.

---

*Structure analysis: 2025-05-15*

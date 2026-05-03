# Technology Stack

**Analysis Date:** 2025-05-14

## Languages

**Primary:**
- TypeScript 5.8.3 - Web application frontend and API routes (`web/src/`)
- Python 3.12 - Core scraping engine and data processing (`scraper/`)

**Secondary:**
- SQL - Database migrations and schema definitions (`db/migrations/`, `web/db/schema.ts`)
- Shell (Bash) - Deployment and migration scripts (`scripts/`)

## Runtime

**Environment:**
- Node.js (Version managed by `web/package.json`)
- Python 3.12 (Managed via `uv` in `scraper/`)

**Package Manager:**
- npm (Web) - Lockfile: `web/package-lock.json`
- uv (Scraper) - Lockfile: `scraper/uv.lock`

## Frameworks

**Core:**
- Next.js 14.2.29 - Web framework (`web/`)
- React 18.3.1 - UI library (`web/src/`)
- Playwright 1.44 - Browser automation for scraping (`scraper/browser.py`)

**Testing:**
- Vitest 4.1.4 - Web unit and integration testing (`web/vitest.config.ts`)
- Pytest 8.0 - Scraper testing (`scraper/pyproject.toml`)

**Build/Dev:**
- Tailwind CSS 3.4.17 - Utility-first CSS framework (`web/tailwind.config.ts`)
- Drizzle ORM 0.36.4 - TypeScript ORM (`web/db/`)
- PostCSS 8.5.3 - CSS transformations (`web/postcss.config.js`)

## Key Dependencies

**Critical:**
- `anthropic` >= 0.28 - AI-powered data extraction and remapping (`scraper/ai_parse.py`)
- `psycopg` [binary] >= 3.2 - PostgreSQL adapter for Python (`scraper/db.py`)
- `postgres` ^3.4.5 - PostgreSQL client for TypeScript (`web/db/index.ts`)
- `httpx` >= 0.27 - Async HTTP client for scraping (`scraper/http_client.py`)
- `beautifulsoup4` >= 4.12 - HTML parsing (`scraper/pyproject.toml`)

**Infrastructure:**
- `drizzle-kit` ^0.28.1 - Migration toolkit for Drizzle ORM (`web/drizzle.config.ts`)

## Configuration

**Environment:**
- `.env` files for local development (Not committed, examples in `.env.example`, `web/.env.local.example`)
- `DATABASE_URL` - Main database connection string
- `ANTHROPIC_API_KEY` - API key for Claude AI services

**Build:**
- `web/next.config.mjs` - Next.js configuration
- `web/tsconfig.json` - TypeScript configuration
- `scraper/pyproject.toml` - Python project configuration

## Platform Requirements

**Development:**
- Node.js
- Python 3.12+
- `uv` (recommended for Python package management)

**Production:**
- Azure Static Web Apps (Frontend + API)
- Supabase (PostgreSQL Database)

---

*Stack analysis: 2025-05-14*

# External Integrations

**Analysis Date:** 2025-05-14

## APIs & External Services

**AI Services:**
- Anthropic Claude - Used for intelligent parsing of course data and remapping university-specific fields.
  - SDK/Client: `anthropic` (Python)
  - Auth: `ANTHROPIC_API_KEY`
  - Models: `claude-3-5-haiku-20241022`, `claude-haiku-4-5-20251001` (experimental)

**University Websites:**
- Various Australian University Sites - Targeted for scraping course details.
  - Implementation: `scraper/base_scraper.py`, `scraper/browser.py`
  - Client: `httpx`, `playwright`

## Data Storage

**Databases:**
- Supabase (PostgreSQL) - Central data store for universities, courses, and scraper configurations.
  - Connection: `DATABASE_URL`
  - Client: `psycopg` (Python), `drizzle-orm` / `postgres.js` (TypeScript)

**File Storage:**
- Local Filesystem - Used for caching snapshots of scraped pages.
  - Location: `scraper/snapshots/`
  - Implementation: `scraper/snapshot_manager.py`

**Caching:**
- Local snapshot-based caching for scraper runs to avoid redundant network requests.

## Authentication & Identity

**Auth Provider:**
- Azure Static Web Apps (Built-in) - Handles user authentication for the web platform.
  - Implementation: `web/src/contexts/auth-context.tsx`
  - Endpoint: `/.auth/me`

## Monitoring & Observability

**Error Tracking:**
- Custom logging to PostgreSQL - Scraper issues are logged to the `atar_issues` table.
  - Implementation: `scraper/db.py` (`log_atar_issue`)

**Logs:**
- Console-based logging in both Scraper and Web applications.

## CI/CD & Deployment

**Hosting:**
- Azure Static Web Apps - Hosts the Next.js application and provides serverless API routes.
  - Configuration: `staticwebapp.config.json`

**CI Pipeline:**
- GitHub Actions - Automates testing and deployment.
  - Workflows: `.github/workflows/scraper-tests.yml`, `.github/workflows/azure-static-web-apps.yml`

## Environment Configuration

**Required env vars:**
- `DATABASE_URL`: PostgreSQL connection string (Supabase)
- `ANTHROPIC_API_KEY`: API key for Anthropic Claude

**Secrets location:**
- Managed in Azure Static Web Apps environment variables and GitHub Action secrets.

## Webhooks & Callbacks

**Incoming:**
- None detected.

**Outgoing:**
- None detected.

---

*Integration audit: 2025-05-14*

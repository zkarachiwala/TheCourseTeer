# The Courseteer

An Australian undergraduate course aggregator and search engine. Aggregates undergraduate course data from all Australian universities into a unified, searchable interface.

## Local Development

**Prerequisites:** [dbmate](https://github.com/amacneil/dbmate)

1. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Update DATABASE_URL in .env with your Supabase connection string.
   # Ensure sslmode=require is present.
   ```

2. **Database:**
   This project strictly uses **Supabase** for its database. For both local development and production, you must point `DATABASE_URL` to your Supabase instance.
   - Recommended: Use the Transaction Pooler (port 6543).

3. **Running migrations:**
   ```bash
   scripts\migrate.bat        # Windows
   bash scripts/migrate.sh    # bash/Mac
   ```
   Migrations live in `db/migrations/`. dbmate tracks applied migrations automatically and reads `DATABASE_URL` from `.env`.

---

## What it does

- Collects course data (name, faculty, campus, ATAR, fees, prerequisites, duration) from Australian university websites
- Uses an AI-adaptive scraper that self-heals when university websites change layout
- Provides a fast, filterable search interface for students comparing courses across universities

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), Tailwind CSS, next-themes |
| Database | PostgreSQL (Supabase) |
| Scraper | Python, Playwright |
| Scraper AI | Local LLM via Ollama (fallback: Claude Haiku) |

## Project status

Phase 1 (MVP) in progress. See `planning/PLAN.md` for the full technical specification.

| Component | Status |
|---|---|
| Database schema | Complete — all tables migrated and seeded |
| Scraper infrastructure | Complete — base scraper, robots.txt compliance, AI re-mapping framework |
| RMIT scraper | Complete |
| La Trobe scraper | Complete |
| ACU scraper | Complete |
| Deakin, Melbourne, Monash, others | Not started |
| Next.js frontend | In progress |

## License

MIT — see [LICENSE](LICENSE).

<p align="center">
  <img src="media/CoureTeerLogo_ImageOnlyV2.png" alt="The Courseteer" width="120" />
</p>

# The Courseteer

An Australian undergraduate course aggregator and search engine. Students currently have to visit a dozen different university websites to compare courses, fees, and ATAR requirements. The Courseteer pulls all of that into one place.

## How it works

- An AI-adaptive scraper collects course data (name, faculty, campus, ATAR, fees, prerequisites, duration) from Australian university websites
- If a university redesigns their site and selectors break, the scraper uses an LLM to re-map fields automatically
- A fast, filterable search interface lets students compare courses across universities in one view

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), Tailwind CSS, next-themes |
| Database | PostgreSQL (Supabase) |
| Scraper | Python, Playwright |
| Scraper AI | Local LLM via Ollama (fallback: Claude Haiku) |

## Scraper coverage

Victorian universities are the Phase 1 focus.

| University | Status |
|---|---|
| RMIT | Complete |
| La Trobe | Complete |
| ACU | Complete |
| Monash | In progress |
| University of Melbourne | In progress |
| Swinburne | In progress |
| Federation University | In progress |
| Victoria University | In progress |
| Deakin | Planned |
| All other Australian universities | Phase 2 |

## Local development

**Prerequisites:** [dbmate](https://github.com/amacneil/dbmate)

1. **Environment setup:**
   ```bash
   cp .env.example .env
   # Set DATABASE_URL to your Supabase connection string (sslmode=require)
   ```

2. **Database:** This project uses Supabase for both local dev and production. Point `DATABASE_URL` at your Supabase instance — Transaction Pooler on port 6543 is recommended.

3. **Run migrations:**
   ```bash
   scripts\migrate.bat        # Windows
   bash scripts/migrate.sh    # macOS/Linux
   ```
   Migrations live in `db/migrations/`. dbmate tracks applied migrations and reads `DATABASE_URL` from `.env`.

4. **Run the scraper:**
   ```bash
   cd scraper
   uv run python run.py --university rmit
   ```

## Project status

Phase 1 (Victorian universities) in progress. See [`planning/PLAN.md`](planning/PLAN.md) for the full technical specification.

| Component | Status |
|---|---|
| Database schema | Complete |
| Scraper infrastructure | Complete — robots.txt compliance, snapshot caching, AI re-mapping |
| Victorian university scrapers | In progress (8 of 9 configured) |
| Next.js frontend | In progress |

## License

MIT — see [LICENSE](LICENSE).

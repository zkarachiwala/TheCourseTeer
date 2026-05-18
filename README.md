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

### Phase 1 — Victorian universities (complete)

| University | Status |
|---|---|
| RMIT | Complete |
| University of Melbourne | Complete |
| Monash University | Complete |
| La Trobe University | Complete |
| Swinburne University of Technology | Complete |
| Federation University | Complete |
| Victoria University | Complete |
| Australian Catholic University (ACU) | Complete |
| Deakin University | Complete |

### Phase 2 — All other Australian universities

| University | Status |
|---|---|
| University of Sydney | Planned |
| University of Queensland | Planned |
| All remaining universities | Planned |

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

Phase 1 (Victorian universities) is complete. Phase 2 expands coverage to all remaining Australian universities.

| Component | Status |
|---|---|
| Database schema | Complete |
| Scraper infrastructure | Complete — robots.txt compliance, snapshot caching, AI re-mapping |
| Victorian university scrapers | Complete — all 9 universities |
| Next.js frontend | Complete — course listings, filters, pagination, campus/ATAR display |
| Admin health dashboard | Complete |
| Authentication (multi-provider) | Complete |
| Phase 2 scrapers | Planned |

## License

MIT — see [LICENSE](LICENSE).

# The Courseteer

An Australian university course aggregator and search engine. Aggregates undergraduate and postgraduate course data from all Australian universities into a unified, searchable interface.

## Local Development

**Prerequisites:** Docker Desktop

```bash
cp .env.example .env
scripts\up.bat        # Windows
bash scripts/up.sh    # bash/Mac
```

- Postgres 17 on `localhost:5432`
- Adminer (DB browser) on `http://localhost:8080` — select **PostgreSQL**, server `db`, credentials from your `.env`

| Action | Windows | bash/Mac |
|---|---|---|
| Start services | `scripts\up.bat` | `bash scripts/up.sh` |
| Stop services | `scripts\down.bat` | `bash scripts/down.sh` |
| Open psql shell | `scripts\psql.bat` | `bash scripts/psql.sh` |
| Tail logs | `scripts\logs.bat` | `bash scripts/logs.sh` |

**Production:** swap `DATABASE_URL` in `.env` for the Supabase connection string (change `sslmode=disable` to `sslmode=require`). No other changes needed.

### Running migrations

Install dbmate once: `winget install dbmate` (Windows) or `brew install dbmate` (Mac).

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
- Tracks UG-to-Masters course pathways

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), Tailwind CSS, next-themes |
| Database | PostgreSQL (Supabase) |
| Scraper | Python, Playwright |
| Scraper AI | Local LLM via Ollama (fallback: Claude Haiku) |
| Scraper API | FastAPI |

## Project status

Early development. See `planning/PLAN.md` for the full technical specification.

## License

MIT — see [LICENSE](LICENSE).

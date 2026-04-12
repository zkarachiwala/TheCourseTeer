# The Courseteer

An Australian university course aggregator and search engine. Aggregates undergraduate and postgraduate course data from all Australian universities into a unified, searchable interface.

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

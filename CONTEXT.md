# The Courseteer — Shared Project Context

An Australian undergraduate course aggregator and search engine. Aggregates course data (name, faculty, campus, ATAR, fees, prerequisites, duration) from all Australian university websites into a unified, searchable interface.

All project documentation is in the `planning` directory. The key document is `planning/PLAN.md`.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), Tailwind CSS, next-themes |
| Database | PostgreSQL (Supabase) — migrations via dbmate in `db/migrations/` |
| Scraper | Python, Playwright, uv |
| ORM | Drizzle (web), psycopg3 (scraper) |

---

## Standards

@docs/standards/ios-icons.md
@docs/standards/code-style.md
@docs/standards/quality-and-testing.md
@docs/standards/data-conventions.md
@docs/standards/scraper-conventions.md

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

## iOS & App Icon Standards

- **Transparency:** iOS (apple-touch-icon) does NOT support transparency. Transparent areas default to solid black.
- **Backgrounds:** Always use a solid background color (e.g. white or brand primary) and flatten the alpha channel.
- **Format:** Square PNGs, 180×180 standard (600×600+ for high quality). iOS applies rounded corners automatically.
- **Workflow:** When asked to generate or update iOS icons, confirm the desired background color before implementation.

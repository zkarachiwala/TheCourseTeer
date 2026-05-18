# The Courseteer - An Australian undergraduate course aggregator and search engine

All project documentation is in the `planning` directory. The key document is `planning/PLAN.md`.

---

## Role

Gemini CLI handles well-specified, mechanical tasks that do not require full codebase context. All architecture decisions, multi-file debugging, and critical code review stay with Claude Code.

Invoke via:
```bash
gemini -m gemini-2.5-flash -p "<task>"
```

Use `gemini-2.5-pro` only when a larger context window is needed.

---

## What to delegate here

- Generating boilerplate: Next.js pages, API routes, Tailwind components
- Writing scraper extraction logic for a single university (given the HTML structure)
- Writing unit tests for a specified function or module
- Generating SQL migration files from a schema description
- Drafting config files: `.env.example`, CI yaml, `pyproject.toml`

All output should be reviewed and integrated by Claude Code before committing.

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

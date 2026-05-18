# Gemini CLI — The Courseteer

@CONTEXT.md

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

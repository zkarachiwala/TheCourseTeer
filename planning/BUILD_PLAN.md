# Build Plan: AI Tool Strategy

How to use available AI tools efficiently to avoid hitting daily limits during development.

---

## Available Tools

| Tool | Model | Daily / Rate Limit | Cost |
|---|---|---|---|
| Claude Code (Pro) | Claude Sonnet 4.6 / Opus 4.6 | ~45 msgs / 5 hrs (Opus); higher on Sonnet | Included in Pro |
| Gemini CLI | Gemini 2.5 Flash | Free tier available | Free |
| Gemini CLI | Gemini 2.5 Pro | Free tier available (use sparingly) | Free |
| OpenCode + Ollama | Mistral / Llama 3 / Gemma (local) | Unlimited | Free (local compute) |

---

## Strategy: Route Tasks by Complexity

Reserve Claude Code for high-value, high-context work. Offload routine and mechanical tasks to Gemini CLI and Ollama.

### Claude Code (Pro) — Use for:
- Architecture decisions and design reviews
- Complex debugging where full codebase context is needed
- Scraper AI re-mapping logic (requires reasoning over HTML structure)
- Code review of critical paths (schema migrations, data integrity)
- Any task requiring multi-file context or reasoning across the full repo

**When to switch away:** When approaching the 5-hour usage limit, switch to Gemini CLI for the next task and return to Claude for the next session window.

### Gemini CLI — Use for:
- Boilerplate generation: Next.js pages, API routes, Tailwind components
- Writing scraper extraction logic for individual universities
- Writing unit tests
- Generating SQL migration files from the schema spec
- Drafting config files: `.env.example`, CI yaml
- Any well-specified task that does not require deep repo context

Use `gemini-2.5-flash` by default. Drop to `gemini-2.5-pro` only when a larger context window is needed (use sparingly).

### OpenCode + Ollama — Use for:
- Scraper AI re-mapping during local development (zero API cost)
- Offline development sessions
- Prompt engineering experiments for HTML field extraction without burning quota

OpenCode configured with Ollama as its backend. No Gemini inside OpenCode — the Gemini CLI handles that separately.

**Recommended Ollama models:**
- `mistral` — good at structured extraction, small footprint
- `llama3.2` — stronger reasoning, suitable for re-mapping logic

---

## Daily Workflow Pattern

```
Morning session (fresh Claude limits):
  -> Claude Code for architecture, complex features, code review

Mid-session (Claude approaching limit):
  -> Gemini CLI for boilerplate, tests, config

If Gemini rate-limited (>1,500 req/day):
  -> OpenCode + Ollama for remaining tasks

Next 5-hour window resets:
  -> Return to Claude Code for the next complex task
```

---

## Cost Exposure Summary

| Task | Tool | Expected cost |
|---|---|---|
| Scraper AI re-mapping (prod) | Ollama (free) or Claude Haiku (~$0.001/call) | Near zero |
| Development & coding | Claude Pro + Gemini CLI free | Included / $0 |
| Supabase database | Supabase free tier | $0 until >500MB |

No significant API spend expected during MVP development.

---

## Setup Checklist

- [x] Claude Code installed
- [x] Gemini CLI installed
- [x] Ollama installed
- [x] OpenCode CLI installed
- [x] OpenCode configured to use Ollama backend
- [x] Ollama model pulled: `ollama pull mistral`
- [x] Supabase project created, connection string saved to `.env`

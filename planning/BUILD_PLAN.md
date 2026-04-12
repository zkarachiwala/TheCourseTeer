# Build Plan: AI Tool Strategy

How to use available AI tools efficiently to avoid hitting daily limits during development.

---

## Available Tools

| Tool | Model | Daily / Rate Limit | Cost |
|---|---|---|---|
| Claude Code (Pro) | Claude Sonnet 4.6 / Opus 4.6 | ~45 msgs / 5 hrs (Opus); higher on Sonnet | Included in Pro |
| Google Gemini (free tier) | Gemini 2.0 Flash | 1,500 req/day, 15 RPM | Free |
| Google Gemini (free tier) | Gemini 1.5 Pro | 50 req/day, 2 RPM | Free |
| OpenCode | Any backend (Gemini, Anthropic, Ollama) | Depends on configured backend | Free (OSS) |
| Ollama (local) | Mistral / Llama 3 / Gemma | Unlimited | Free (local compute) |

---

## Strategy: Route Tasks by Complexity

The goal is to reserve Claude (Pro) for high-value, high-context work and offload routine or mechanical tasks to free tiers and local models.

### Claude Code (Pro) — Use for:
- Architecture decisions and design reviews
- Complex debugging where full codebase context is needed
- Scraper AI re-mapping logic (requires reasoning about HTML structure)
- Code review of critical paths (auth, data integrity, schema migrations)
- Any task requiring multi-file context or reasoning across the full repo

**When to switch away:** If you are hitting the 5-hour usage limit, switch to Gemini or OpenCode for the next task and return to Claude for the next session.

### Google Gemini 2.0 Flash (free tier via OpenCode) — Use for:
- Boilerplate generation: Next.js pages, API routes, Tailwind components
- Writing and iterating on scraper extraction logic for individual universities
- Writing unit tests
- Generating SQL migration files from the schema spec
- Drafting `.env.example` files, Docker Compose configs, CI yaml
- Any task that is well-specified enough that it can be handed off without deep context

**How to access:** Configure OpenCode to use the Gemini API backend with your Google AI Studio API key (free at aistudio.google.com). Use `gemini-2.0-flash` as the model — it has the highest free daily limit (1,500 req/day) and is fast enough for routine code generation.

### Gemini 1.5 Pro (free tier) — Use for:
- Larger context tasks: analyzing a full university HTML page to identify fields
- Reviewing a full module or file for issues
- Use sparingly — only 50 req/day free

### OpenCode — How to configure:
OpenCode is a terminal-based coding assistant that supports pluggable LLM backends. Install it and configure backends in priority order:

```
1. Gemini 2.0 Flash  (free, fast — default for routine work)
2. Ollama local      (free, offline — for scraper AI re-mapping in dev)
3. Claude Haiku      (paid, cheap per-call — fallback if Gemini is rate-limited)
```

Configuration file: `~/.config/opencode/config.json` (exact path depends on OS).

### Ollama (local) — Use for:
- Scraper AI re-mapping during local development (avoids any API cost)
- Offline development sessions
- Experimenting with prompt engineering for HTML field extraction without burning API quota

**Recommended models:**
- `mistral` — good at structured extraction tasks, small footprint
- `llama3.2` — stronger reasoning, larger but capable on modern hardware
- `gemma3` — Google's OSS model, good balance of size and capability

Install: `winget install Ollama.Ollama` then `ollama pull mistral`

---

## Daily Workflow Pattern

```
Morning session (fresh Claude limits):
  -> Use Claude Code for architecture, complex features, code review

Mid-session (Claude approaching limit):
  -> Switch to OpenCode + Gemini 2.0 Flash for boilerplate, tests, config

If Gemini rate-limited (>1,500 req):
  -> Drop to OpenCode + Ollama local for remaining tasks

Next 5-hour window resets:
  -> Return to Claude Code for the next complex task
```

---

## Cost Exposure Summary

For the MVP build, the only tasks likely to incur cost are:

| Task | Tool | Expected cost |
|---|---|---|
| Scraper AI re-mapping (prod) | Ollama (free) or Claude Haiku (~$0.001/call) | Near zero |
| Development & coding | Claude Pro (flat rate) + Gemini free | Included / $0 |
| Supabase database | Supabase free tier | $0 until >500MB or >2 projects |

No significant API spend is expected during MVP development if the routing above is followed.

---

## Setup Checklist

- [ ] Get Google AI Studio API key at aistudio.google.com (free, no credit card)
- [ ] Install OpenCode and configure Gemini backend
- [ ] Install Ollama: `winget install Ollama.Ollama`
- [ ] Pull a local model: `ollama pull mistral`
- [ ] Test Ollama is working: `ollama run mistral "hello"`
- [ ] Create Supabase project and save connection string to `.env`

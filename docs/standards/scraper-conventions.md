# Scraper Conventions

## Two Scraper Modes

Every university scraper operates in one of two modes, set in `seed_site_configs.py`:

| Mode | When to use | Implementation |
|---|---|---|
| `static` | Data is present in raw HTML (no JS rendering required) | `httpx` + `BeautifulSoup` — fast, no browser launch |
| `browser` | Data is rendered client-side or hidden behind JS interactions | Playwright — required for SPAs, accordion tabs, dynamic content |

Use `static` wherever possible. Only use `browser` when static extraction returns empty or incomplete data.

**Current mode by university:**

| University | Mode | Reason |
|---|---|---|
| RMIT | static | ATAR and fees in raw HTML attributes |
| Monash | static | Fee data in inline `<script>` JSON block |
| La Trobe | static | Data in JSON embedded in page |
| Swinburne | static | |
| Federation | static | |
| ACU | static | |
| University of Melbourne | browser | Nuxt.js SPA — all data rendered client-side |
| Victoria University | browser | |
| Deakin | browser / JSON API | Cloudflare-protected; uses JSON API endpoint |

---

## AI Re-mapping (Self-Healing)

When a CSS selector throws an exception, the scraper triggers AI re-mapping:

1. **Try Ollama first** (local, free) — model: `llama3`
2. **Fall back to Claude Haiku** if Ollama is unavailable or errors — model: `claude-haiku-4-5-20251001`

The failing selector and its AI-generated replacement are both stored in `scraper_configs` with `ai_generated = true` for auditability.

**Note:** GitHub Actions runners have no local Ollama. Re-mapping on CI falls through directly to Claude Haiku. Running locally keeps Ollama available and avoids API cost.

---

## Re-mapping Trigger

Exception-based only. If a selector raises an exception during extraction, immediately trigger a re-mapping attempt. Do not pre-emptively re-map on empty results (empty is a valid outcome for some fields).

---

## Snapshot Caching

The scraper caches fetched HTML to `scraper/snapshots/` (gitignored) to avoid redundant requests during development and testing.

- `--no-cache` flag bypasses the cache
- `--refresh` flag forces a fresh fetch and overwrites the cache
- Cache TTL: configurable via `ttl_days` in `SnapshotManager`

Gold-standard test fixtures in `scraper/tests/gold_standards/fixtures/` are committed snapshots used for regression testing. These are not managed by `SnapshotManager` — they are static and version-controlled.

---

## Undergraduate Filter

All scrapers must filter out postgraduate courses before upserting. See [`data-conventions.md`](data-conventions.md) for the filter rules.

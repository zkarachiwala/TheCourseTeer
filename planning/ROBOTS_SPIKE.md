# Spike: robots.txt Compliance & Data Acquisition Strategy

**Date:** 2026-04-13
**Scope:** 5 MVP universities — Melbourne, Sydney, RMIT, Monash, UQ

---

## TL;DR

All 5 universities **allow scraping of course/handbook pages** in their robots.txt. The challenge is not legal compliance — it is technical: two sites use JavaScript rendering and two are behind Cloudflare bot protection. No PDF brochure extraction is needed for the MVP universities.

---

## Findings Per University

### 1. University of Melbourne — unimelb.edu.au

| Item | Finding |
|---|---|
| robots.txt accessible? | Yes (requires browser User-Agent — Cloudflare blocks curl default) |
| Course pages blocked? | No |
| Notable disallows | /_assets/, /templates/, /home-new/, /design/, /staffdev/ |
| Page rendering | Nuxt.js SPA (`window.__NUXT__` detected on study.unimelb.edu.au) |
| JSON-LD / Schema.org | None found |
| ATAR/fees in static HTML | No — data rendered client-side by Nuxt |
| Bot protection | Cloudflare (managed challenge on main domain) |

**Extraction approach:** Playwright required. Nuxt.js renders all course data client-side via JavaScript. Static HTML scraping will return an empty shell. Playwright with a real browser fingerprint will bypass Cloudflare.

**Risk:** Medium-High. Cloudflare may trigger challenges even with Playwright. May need to investigate if study.unimelb.edu.au makes API calls that can be intercepted directly.

---

### 2. University of Sydney — sydney.edu.au

| Item | Finding |
|---|---|
| robots.txt accessible? | Yes (no bot protection) |
| Course pages blocked? | No |
| Notable disallows | /handbooks/archive/2011/, /search/, library assets, agent portal PDFs |
| Page rendering | Server-rendered HTML (no SPA framework detected) |
| JSON-LD / Schema.org | None found |
| ATAR/fees in static HTML | Not present — likely behind JS tabs/accordions |
| Bot protection | None detected |

**Extraction approach:** Playwright required to click through accordion/tab panels that reveal ATAR and fee data. The page shell loads server-side, but the data fields appear to be toggled via JavaScript. Static scraping will get course name and description only.

**Risk:** Low-Medium. No bot protection, but JS interaction is needed to expose data.

---

### 3. RMIT — rmit.edu.au

| Item | Finding |
|---|---|
| robots.txt accessible? | Yes (no bot protection) |
| Course pages blocked? | No |
| Notable disallows | /search?*, /archived/programs/, old news (2014–2017), RSS feeds |
| Page rendering | Server-rendered HTML |
| JSON-LD / Schema.org | None found |
| ATAR/fees in static HTML | **Yes** — ATAR in `data-level` attributes (32 references), fees in `name="fees_domestic"` fields (27 references) |
| Bot protection | None detected |
| Course URL pattern | `/study-with-us/levels-of-study/undergraduate-study/bachelor-degrees/[name]-[code]` |

**Extraction approach:** Static HTML scraping — no Playwright needed. ATAR and fee data are present in the raw HTML. CSS selectors targeting `data-level` and `name="fees_domestic"` attributes will extract values reliably.

**Risk:** Low. Best case in the MVP set for straightforward scraping.

---

### 4. Monash University — monash.edu

| Item | Finding |
|---|---|
| robots.txt accessible? | Yes (requires browser User-Agent — Cloudflare on main domain) |
| Course pages blocked? | No |
| Notable disallows | CMS admin paths, dev/staging paths, search, old department paths |
| Page rendering | Server-rendered HTML (no SPA detected) |
| JSON-LD / Schema.org | Yes — `Course` type with name and description only (no ATAR/fees) |
| ATAR/fees in static HTML | **Yes** — fee data as inline JSON: `"CSP": "A$14,500"`, `"FeeDomesticFullFee": "A$38,000"`, `"FeeInternationalFullFee": "A$55,000"`. ATAR present in 72 HTML references. |
| Bot protection | Cloudflare (main domain — resolved with browser User-Agent) |
| Course URL pattern | `/study/courses/find-a-course/[name]-[code]` |

**Extraction approach:** Static HTML + inline JSON extraction. Fee data is embedded as a JSON object in a `<script>` tag (not ld+json — a data layer object). Regex or JSON parsing of that script block gives exact CSP and full-fee prices. ATAR data is in HTML. No Playwright needed.

**Risk:** Low-Medium. Cloudflare resolves with a browser User-Agent in the HTTP request — Playwright's default headers are sufficient. No JS rendering required for data.

---

### 5. University of Queensland — uq.edu.au

| Item | Finding |
|---|---|
| robots.txt accessible? | Yes (no bot protection) |
| Course pages blocked? | No |
| Notable disallows | /study/search.html, /search/ only |
| Page rendering | Server-rendered HTML |
| JSON-LD / Schema.org | **Yes** — `Course` type with name, description, courseCode, educationalCredentialAwarded |
| ATAR/fees in static HTML | ATAR: link references present. Fees: "annual fee" mentioned in HTML. Amounts appear to be loaded dynamically. |
| Bot protection | None |
| Course URL pattern | `/study/program.html?acad_prog=[code]` |

**Extraction approach:** Hybrid. JSON-LD gives course identity fields for free. ATAR and exact fee amounts are not in JSON-LD and appear to require Playwright to load the full page content (dynamic tabs likely).

**Risk:** Low for basic fields. Medium for ATAR/fee amounts.

---

## Summary Table

| University | robots.txt OK | Bot Protection | Rendering | ATAR in HTML | Fees in HTML | Playwright Needed |
|---|---|---|---|---|---|---|
| Melbourne | Yes | Cloudflare | Nuxt.js SPA | No | No | Yes (required) |
| Sydney | Yes | None | Server HTML | No (JS tabs) | No (JS tabs) | Yes (for full data) |
| RMIT | Yes | None | Server HTML | Yes | Yes | No |
| Monash | Yes | Cloudflare (UA) | Server HTML | Yes | Yes (inline JSON) | No |
| UQ | Yes | None | Server HTML | Partial | Partial | Yes (for amounts) |
| ACU | TBD | TBD | TBD | TBD | TBD | TBD |

---

## Recommended Scraper Architecture (Revised)

Based on these findings, a single Playwright-based scraper handles all cases — but for RMIT and Monash (where data is in static HTML), Playwright is optional overhead. The recommended approach is:

**Two scraper modes:**

1. **Static mode** (RMIT, Monash): Use `httpx` + `BeautifulSoup` for fast, lightweight extraction. No browser launch needed. Faster, cheaper, no Playwright dependency for these two.

2. **Browser mode** (Melbourne, Sydney, UQ): Use Playwright to render JS and interact with dynamic elements. Required for Nuxt.js (Melbourne) and JS accordion tabs (Sydney, UQ).

The `scraper_configs` table should include a `mode` field: `static` or `browser`.

---

## PDF Brochure Extraction

**Not needed for MVP.** All 5 universities expose course data in HTML. PDF extraction is a fallback for Phase 2 when expanding to smaller universities that may not have structured web pages.

---

## Open Issues to Monitor

- **ACU Assessment**: ACU has been added to the Victorian university list. A scraping spike is required to determine rendering mode and data availability.
- **Melbourne Cloudflare**: If Cloudflare escalates from User-Agent check to full managed challenge (JS fingerprinting), even Playwright may be blocked. Monitor during initial scraper runs. Mitigation: Playwright stealth plugin, or check if an undocumented API powers the Nuxt.js frontend (intercept XHR calls).
- **UQ dynamic data**: ATAR guarantee and exact annual fees are referenced but amounts not confirmed in static HTML. Verify with Playwright run.
- **RMIT URL discovery**: Course list page only surfaces ~7 links in static HTML — a sitemap or search API will be needed to enumerate all RMIT courses.

# Plan Review - Clarifications & Decisions Required

## Summary

The plan is well-structured and the competitive angle is clear. The main risk to build efficiency is scope ambiguity in the data model and the AI scraper design. Decisions below should be locked before implementation starts.

---

## 1. Tech Stack - Decisions Needed

### 1.1 Frontend: Next.js vs React
**Question:** The plan says "Next.js or React." Which is it?
**Recommendation:** Next.js. It gives SSR/SSG for SEO (students searching Google), and `next-themes` is designed for it. React-only requires extra setup for the same result.
**Decision needed:** Confirm Next.js App Router (v14+).
ANSWER: Next.js App Router confirmed. This allows for Server Components, which can query the database directly without a separate API layer for read operations, simplifying the architecture.

### 1.2 Backend / API Layer
**Question:** There is no mention of a backend API. The scraper writes to Postgres. The frontend reads from... what?
**Options:**
- Next.js API routes (simplest, co-located with the frontend)
- Separate FastAPI service in Python (keeps scraper and API in the same language)
- No explicit API; Next.js Server Components query Postgres directly via an ORM
**Recommendation:** Next.js Server Components + a thin Python FastAPI for scraper management. Avoids duplicating database access logic.
**Decision needed:** Confirm API strategy before schema work.
ANSWER: Use recommendation

### 1.3 LLM for AI Scraper
**Question:** "GPT-4o-mini or a specialized BERT model" - these are very different in cost, latency, and capability.
- BERT/fine-tuned models: fast, cheap, but require labelled training data we don't have yet.
- GPT-4o-mini (or Claude Haiku): zero-shot capable, API cost per re-mapping event is low, no training data needed.
**Recommendation:** Start with Claude Haiku (`claude-haiku-4-5-20251001`) for re-mapping logic. It is cheaper than GPT-4o-mini and we already have the SDK context. Drop BERT entirely for MVP.
**Decision needed:** Confirm LLM choice before scraper work starts.
ANSWER: Determine if there is a low cost or free option for LLM usage, such as an open-source model that can be hosted locally, to minimize costs during development and testing. If not, proceed with Claude Haiku as recommended.

---

## 2. Data Schema - Gaps to Fill

### 2.1 University entity
The plan lists university as a field on Course, not its own entity. This will create data integrity issues (typos, duplicate names). A `universities` table is needed with at minimum: `id`, `name`, `slug`, `homepage_url`, `scraper_status`.
ANSWER: Agreed. A `universities` table will be created to ensure data integrity and allow for easier management of university-specific information, such as scraper status and homepage URL.

### 2.2 Price: what exactly is stored?
"Domestic pricing" is ambiguous. Australian undergraduate pricing is per-year, per-unit, or total? CSP (Commonwealth Supported Place) is the dominant model and is set by the government in bands, not by the university. Full-fee postgraduate pricing is set by the university.
**Questions:**
- Are we storing indicative annual cost, total course cost, or per-unit cost?
- CSP vs DFEE as a flag, or two separate price fields?
- Do we store the Commonwealth contribution (the government's share) or just the student contribution band?
**Recommendation:** Store `price_annual_csp_aud`, `price_annual_dfee_aud` (nullable), `csp_available` (boolean). Total cost can be derived from duration.
ANSWER: As recommended

### 2.3 ATAR: "Lowest Selection Rank" vs "Guaranteed Entry"
ADVANTAGE.md correctly flags this. The schema needs two separate fields: `atar_guaranteed` and `atar_lowest_selection_rank`. Many universities only publish one of these; both should be nullable.
ANSWER: As recommended

### 2.4 State prerequisite subjects
VCE/HSC/QCE etc. subjects as prerequisites — are these stored as free text, a structured list, or a normalised subjects table?
**Recommendation:** For MVP, store as JSONB array of strings (e.g. `["English (any)", "Maths Methods"]`). Normalise in Phase 2 if prerequisite mapping becomes a feature.
ANSWER: As recommended as long as these are standardised across universities. If there is significant variation in how prerequisites are listed, we may need to normalise sooner.

### 2.5 Course-to-Course relationship (UG -> Masters pathway)
ADVANTAGE.md says this is a key differentiator. The current schema has no `course_relationships` table.
**Recommendation:** Add `course_prerequisites (course_id, requires_course_id, notes)` table to schema from the start, even if it's empty in MVP. Retrofitting a relationship table after data is loaded is painful.
ANSWER: As recommended

---

## 3. Scraper Design - Ambiguities

### 3.1 Playwright (Python) vs Puppeteer (Node)
The plan lists both. They cannot both be "the" scraper. Playwright has a Python API; Puppeteer is Node-only.
**Recommendation:** Playwright with Python. Consistent with the Python scraper language, has better async support, and `playwright` is well-maintained.
ANSWER: As recommended

### 3.2 What triggers the AI re-mapping?
"If a previously successful selector fails" - the trigger logic needs definition:
- Option A: Selector throws exception -> immediate re-map attempt.
- Option B: Extracted value is null/empty for N consecutive runs -> trigger re-map.
- Option C: Checksums page structure hash against stored hash -> pre-emptive re-map.
**Recommendation:** Option A for MVP (simplest). Store the failing selector and the AI's replacement in the `scraper_configs` table for auditability.
ANSWER: As recommended

### 3.3 Scraper config storage
Where do selectors/extraction rules live? The plan doesn't say.
**Recommendation:** A `scraper_configs` table in Postgres: `(university_id, field_name, selector, last_verified_at, ai_generated: bool)`. This makes the Health Dashboard trivial to build.
ANSWER: As recommended

### 3.4 robots.txt compliance
ADVANTAGE.md flags this as a legal/compliance requirement. The scraper must check and respect `robots.txt` before crawling. This should be a first-class feature, not an afterthought.
ANSWER: As recommended please log the `robots.txt` rules for each university in the `universities` table, and ensure the scraper checks these rules before attempting to scrape any pages. If scraping is disallowed, log this in the scraper status and skip that university.  We can revisit this if we find that critical data is behind `robots.txt` restrictions, but for MVP we should respect these rules to avoid legal issues.
---

## 4. MVP Scope - Tighten the Definition

Phase 1 says "3-5 major universities." For build efficiency, name them now so we can validate the schema against real data before committing to it.

**Suggested MVP universities** (diverse website architectures, large student population):
1. University of Melbourne (complex, table-based course pages)
2. University of Sydney (uses structured JSON-LD in some pages)
3. RMIT (large postgrad offering, fee structures are complex)
4. Monash University
5. University of Queensland

Each has a different HTML structure, which will stress-test the scraper design early.

---

## 5. Infrastructure - Not Addressed in Plan

### 5.1 Where does Postgres run?
- Local dev: Docker Compose (fine)
- Production: RDS, Supabase, Railway, Neon?
**Recommendation:** Supabase for MVP. Managed Postgres, built-in REST API, free tier sufficient for initial data volume. Switch to RDS if scale demands it.
ANSWER: As recommended

### 5.2 Where does the scraper run?
Playwright requires a real browser. This is heavy for a Lambda/serverless function.
**Recommendation:** A long-running worker process (e.g., a simple Python service on a VPS or Railway worker). Not serverless.
ANSWER: As recommended

### 5.3 Scheduling
"Monthly or quarterly" runs. Who triggers this?
**Recommendation:** A simple cron job on the worker host, or a Celery beat task if the job queue grows complex. Not a separate scheduler service for MVP.
ANSWER: As recommended
---

## 6. Not Blocking - But Note for Later

- **Search:** The plan doesn't specify full-text search. Postgres `tsvector` is sufficient for MVP. Do not add Elasticsearch/Algolia until it's proven necessary.
- **Health Dashboard:** Described as "admin view" — confirm whether this is behind auth or just an internal URL. For MVP, an internal URL is simpler.
- **Data versioning (Section 6):** Storing historical ATAR/price changes is valuable but adds schema complexity. For MVP, a simple `updated_at` timestamp per row is sufficient. Full versioning (e.g., with a `course_history` audit table) can wait until Phase 2.

---

## Decisions Checklist

| # | Decision | Status |
|---|---|---|
| 1 | Frontend: Next.js (App Router) confirmed? | DECIDED: Next.js App Router v14+ |
| 2 | API strategy: Next.js Server Components + FastAPI, or other? | DECIDED: Server Components for reads, FastAPI for scraper management |
| 3 | LLM for scraper? | DECIDED: Investigate local OSS model (Ollama + Mistral/Llama 3) first. Fallback: Claude Haiku |
| 4 | Price schema: annual CSP + DFEE nullable? | DECIDED: price_annual_csp_aud, price_annual_dfee_aud (nullable), csp_available |
| 5 | ATAR schema: two fields (guaranteed + lowest selection rank)? | DECIDED: Both fields, both nullable |
| 6 | Course prerequisites table in schema from day one? | DECIDED: Yes, even if empty in MVP |
| 7 | Playwright (Python only, not Puppeteer)? | DECIDED: Playwright Python |
| 8 | Scraper re-map trigger: exception-based (Option A)? | DECIDED: Option A |
| 9 | Production Postgres host: Supabase? | DECIDED: Supabase |
| 10 | MVP universities: Melbourne, Sydney, RMIT, Monash, UQ? | DECIDED: Confirmed |
| 11 | robots.txt: store rules in universities table, skip if blocked? | DECIDED: Yes, first-class compliance |
| 12 | Scraper config storage: scraper_configs table in Postgres? | DECIDED: Yes |

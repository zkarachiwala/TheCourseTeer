# Codebase Concerns

**Analysis Date:** 2026-05-03

## Tech Debt

**Scraper hardcoding:**
- Issue: `scraper/run.py` hardcodes the mapping of university slugs to scraper classes.
- Files: `scraper/run.py`
- Impact: Adding or removing universities requires code modifications rather than simple configuration.
- Fix approach: Load scraper mappings from the database or use a dynamic discovery pattern based on university records.

**Minimal Error Handling:**
- Issue: Broad exception catching with only print statements for logging.
- Files: `scraper/run.py`, `scraper/universal_engine.py`
- Impact: Errors may go unnoticed without centralized monitoring (e.g., Sentry), making it hard to track scraper health at scale.
- Fix approach: Implement structured logging and integrate an error tracking service.

**Hardcoded Confidence Scores:**
- Issue: Fixed confidence scores (90 for JSON, 70 for HTML) are assigned regardless of data quality.
- Files: `scraper/universal_engine.py`
- Impact: Users cannot distinguish between highly reliable data and data extracted via fragile heuristics.
- Fix approach: Implement a scoring algorithm based on data completeness and selector reliability.

**Campus Link Inefficiency:**
- Issue: Deletes all existing campus associations before re-inserting them on every update.
- Files: `scraper/db.py`
- Impact: Unnecessary database write volume and potential for temporary data inconsistency during the transaction.
- Fix approach: Use a differential update strategy (delta sync) to only insert/delete changed associations.

## Known Bugs

**Latrobe Title Escaping:**
- Symptoms: Escape characters like `\/` appear in course titles.
- Files: `scraper/universal_engine.py`
- Trigger: Scraping courses from La Trobe University with dual-degree names.
- Workaround: Cleaned via `_unescape_text` but needs more robust handling for all edge cases.

**Latrobe Missing ATAR/Duration:**
- Symptoms: Critical data fields are empty for many courses.
- Files: `scraper/universal_engine.py`, `planning/LATROBE.md`
- Trigger: Structure changes on the La Trobe handbook site that the current engine cannot parse.
- Workaround: Manual fixes or AI re-mapping are required.

**Campus ID Resolution:**
- Symptoms: Courses may be missing campuses if resolution fails.
- Files: `scraper/db.py`
- Trigger: Campus name or alias mismatch during the scraping process.
- Workaround: Silent filtering currently happens; needs logging of failed resolutions to `atar_issues`.

## Security Considerations

**Environment Variables:**
- Risk: Potential for accidental commitment of secrets.
- Files: `.env`, `.env.example`
- Current mitigation: `.gitignore` includes `.env` and `.env.local`.
- Recommendations: Use a secret manager (e.g., Azure Key Vault, GitHub Secrets) for production deployments.

**Robots.txt Compliance:**
- Risk: Bypassing crawler blocks when using `browser` mode.
- Files: `scraper/universal_engine.py`, `scraper/robots.py`
- Current mitigation: `robots.py` provides checking logic, but enforcement is manual in the scraper logic.
- Recommendations: Integrate robots checking directly into the `fetch` methods of the base scraper.

## Performance Bottlenecks

**Sequential Scraping:**
- Problem: Universities are scraped one after another.
- Files: `scraper/run.py`
- Cause: Simple loop in the main entry point.
- Improvement path: Parallelize university scraping using `asyncio.gather` while respecting rate limits per host.

**Playwright Overhead:**
- Problem: High resource usage and slow execution in `browser` mode.
- Files: `scraper/browser.py`, `scraper/universal_engine.py`
- Cause: Full browser rendering for each page.
- Improvement path: Use `static` mode (httpx) wherever possible; optimize browser context reuse.

**Database Search:**
- Problem: Search performance may degrade as the course count increases.
- Files: `web/src/app/courses/page.tsx` (implied search logic)
- Cause: Basic Postgres `tsvector` without advanced optimization.
- Improvement path: Add GIN indexes and potentially move to a dedicated search service if performance becomes an issue.

## Fragile Areas

**Regex-based Parsing:**
- Files: `scraper/universal_engine.py`
- Why fragile: High sensitivity to minor formatting changes in ATAR and duration strings.
- Safe modification: Use the `selector` and `SiteConfig` to provide more specific extraction patterns.
- Test coverage: Limited to specific samples; needs more varied test data.

**Anchor-based Extraction:**
- Files: `scraper/universal_engine.py`
- Why fragile: Relies on label proximity which can be inconsistent across different site designs.
- Safe modification: Prefer explicit CSS selectors or JSON-LD metadata.

## Scaling Limits

**Supabase Free Tier:**
- Current capacity: 500MB database, limited connections.
- Limit: Will be reached quickly as full course history and snapshots are stored.
- Scaling path: Upgrade to a paid plan or implement aggressive data retention/archiving policies.

## Dependencies at Risk

**Playwright:**
- Risk: Complex installation and potentially brittle in headless environments.
- Impact: Can break CI/CD pipelines or local setup if versions mismatch.
- Migration plan: Maintain a stable Docker image for scraper execution.

## Missing Critical Features

**Scraper Alerting:**
- Problem: No automated way to know if a scraper is failing without checking the dashboard.
- Blocks: Rapid response to site changes.

**International Student Data:**
- Problem: Only domestic data is currently handled.
- Blocks: Expansion to the international student market.

## Test Coverage Gaps

**Frontend Coverage:**
- What's not tested: Most Next.js components and server actions.
- Files: `web/src/`
- Risk: Regression bugs during UI updates or refactoring.
- Priority: High

**E2E Testing:**
- What's not tested: The complete data pipeline from scrape to display.
- Files: `scraper/`, `web/`
- Risk: Integration failures between the scraper and the web application.
- Priority: Medium

**Mocking External Sites:**
- What's not tested: Real-world browser interactions and handling of various HTTP error codes.
- Files: `scraper/tests/`
- Risk: Scrapers may fail in production in ways not captured by static HTML tests.
- Priority: Medium

---

*Concerns audit: 2026-05-03*

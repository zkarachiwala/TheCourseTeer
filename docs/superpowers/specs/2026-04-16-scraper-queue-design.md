# Scraper Queue Design

**Date:** 2026-04-16
**Status:** Approved

## Problem

Scrape runs are subject to interruption (timeouts, network failures, Cloudflare rate-limiting). The current approach re-discovers and re-fetches everything on each run, with no durable record of what has been attempted or completed. Resuming requires guessing where to continue from.

## Goals

- Store discovered URLs durably before attempting to fetch them.
- On resume (default behaviour), skip completed URLs and continue from where the run left off.
- Retry failed URLs up to a configurable limit (default 3); surface permanently-failed URLs for inspection.
- Track a per-university run sequence number for auditability.
- Support `--force` to reset and re-run a university from scratch.
- Support `--university <slug>` to target a single university.

## Schema

### `scrape_runs` table

One row per scrape run per university.

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| university_id | uuid | FK -> universities ON DELETE CASCADE |
| run_number | int | Per-university sequence (1, 2, 3…) |
| discovery_complete | bool | True once listing page URLs are fully enqueued |
| status | text | `in_progress` / `complete` / `failed` |
| forced | bool | True if started with --force |
| started_at | timestamptz | Default now() |
| completed_at | timestamptz | Nullable |

Unique constraint on `(university_id, run_number)`.
`run_number` is assigned atomically at insert time using a subquery: `INSERT ... SELECT COALESCE(MAX(run_number), 0) + 1 FROM scrape_runs WHERE university_id = $1`. This avoids race conditions if two runs start simultaneously for the same university.

### `scrape_queue` table

One row per discovered URL.

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| university_id | uuid | FK -> universities ON DELETE CASCADE |
| discovered_run_id | uuid | FK -> scrape_runs — run that found this URL |
| completed_run_id | uuid | FK -> scrape_runs, nullable — run that scraped it |
| url | text | |
| status | text | `pending` / `complete` / `failed` |
| attempt_count | int | Default 0 |
| last_error | text | Nullable — most recent exception message |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |

Unique constraint on `(university_id, url)`.

## Scraper Flow

### Normal run (no `--force`)

1. Look for the latest `in_progress` run for this university in `scrape_runs`. If none exists, create a new one, incrementing `run_number`.
2. If `discovery_complete = false`: fetch the listing page, insert all discovered URLs into `scrape_queue` with `status='pending'` using `ON CONFLICT DO NOTHING` (preserves status of any already-queued URLs), then set `discovery_complete = true`.
3. Pull all `pending` queue rows for this university where `attempt_count < 3`. Scrape each one:
   - Success: upsert course, set `status='complete'`, set `completed_run_id` to current run id, set `updated_at=now()`.
   - Failure: increment `attempt_count`, store `last_error`, set `updated_at=now()`. If `attempt_count >= 3`, set `status='failed'`.
4. When no `pending` rows remain, set run `status='complete'` and `completed_at=now()`.

### `--force` run

Delete all `scrape_queue` rows for the university. Create a new `scrape_runs` row with `forced=true`. Proceed as a normal run from step 2.

### Inspecting failed URLs

```sql
SELECT sq.url, sq.attempt_count, sq.last_error, sr.run_number
FROM scrape_queue sq
JOIN scrape_runs sr ON sq.discovered_run_id = sr.id
JOIN universities u ON sq.university_id = u.id
WHERE sq.status = 'failed'
ORDER BY u.slug, sr.run_number;
```

No separate table is needed. The health dashboard (PLAN.md §6) can surface this query.

## Code Changes

### Migration

One new SQL migration file adding `scrape_runs` and `scrape_queue` tables.

### `db.py` — new functions

- `get_or_create_run(pool, university_id, force) -> dict` — finds the latest `in_progress` run or creates a new one. If `force=True`, deletes existing queue rows first.
- `mark_discovery_complete(pool, run_id)`
- `enqueue_urls(pool, university_id, run_id, urls: list[str])` — bulk insert with `ON CONFLICT DO NOTHING`
- `get_pending_urls(pool, university_id, max_attempts=3) -> list[str]`
- `mark_url_complete(pool, university_id, url, run_id)`
- `mark_url_failed(pool, university_id, url, error: str)`
- `complete_run(pool, run_id)`

The existing `get_existing_source_urls` function is no longer needed once the queue is in place; it can be removed.

### `base_scraper.py` — interface change

Split the current single `scrape(rp)` abstract method into two:

- `discover_urls(rp) -> list[str]` — fetches the listing page and returns course URLs. Called only when `discovery_complete = false`.
- `scrape_url(ctx, url) -> CourseData | None` — fetches and parses a single course page.

`BaseScraper.run()` owns the queue orchestration: get/create run, conditionally call `discover_urls`, enqueue, then iterate `get_pending_urls` calling `scrape_url` for each, updating queue status after each attempt.

Concurrency and retry logic moves into `BaseScraper.run()` rather than individual scrapers.

### `monash.py`

Implement `discover_urls` (extracts the listing page URL discovery logic from `_playwright_fetch_all`) and `scrape_url` (wraps `_fetch_page` + `_parse_course`). The Playwright thread-executor workaround remains in `MonashScraper` since it needs `asyncio.run()` in a thread.

### `rmit.py`

Implement `discover_urls` and `scrape_url` following the same split.

### `run.py`

Add CLI flags:
- `--force` — resets queue and re-runs discovery for specified universities.
- `--university <slug>` — run only the named university (can be specified multiple times). Defaults to all registered scrapers.

## Retry Configuration

`MAX_ATTEMPTS = 3` defined as a module-level constant in `base_scraper.py`. Passed to `get_pending_urls`. Can be overridden per-scraper by overriding a class attribute.

## Out of Scope

- Scheduling (remains a cron job per PLAN.md).
- Per-URL retry delays / backoff (can be added later if needed).
- Queue visibility in the web frontend (Phase 2).

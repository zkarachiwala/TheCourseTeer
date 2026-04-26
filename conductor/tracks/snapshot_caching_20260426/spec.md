# Specification: HTML Snapshot Caching System

## Overview
Implement a filesystem-based caching layer for course HTML and auxiliary data (JSON). This system will allow the scraper to store a "snapshot" of a page's content locally, enabling rapid iteration on extraction logic without repeated network requests to university servers.

## Goals
1.  **Reduce Network Load:** Avoid potential IP bans or throttling.
2.  **Speed Up Iteration:** Millisecond-level access to content for testing and debugging.
3.  **Stability for UI:** Provide the Visual Scraper Builder with consistent data.
4.  **Regression Testing:** Enable a "warchest" of real-world HTML for automated tests.

## Functional Requirements
1.  **Storage Structure:**
    -   Root directory: `scraper/snapshots/`.
    -   Sub-directories by University ID or Slug: `scraper/snapshots/<university_id>/`.
    -   Filenames: MD5 or SHA256 hash of the full URL: `<url_hash>.html`.
    -   Metadata: Store timestamp and original URL (possibly as a separate `.json` or header in the file).
2.  **Cache Logic:**
    -   **Read:** Before fetching, check if the snapshot exists.
    -   **TTL (Time-To-Live):** Configurable cache expiration (e.g., 7 days).
    -   **Write:** After a successful fetch, save the content to the snapshot directory.
3.  **Control Flags:**
    -   `USE_CACHE` (bool): Enable/disable the caching layer globally.
    -   `FORCE_REFRESH` (bool): Bypass existing cache and overwrite with fresh data.
4.  **Integration:**
    -   Integrate into `BaseScraper` or a shared `http_client` wrapper.
    -   Support both static HTML (httpx) and dynamic (Playwright) snapshots.
    -   Support auxiliary data (e.g., La Trobe's `follow_urls` JSONs).

## Non-Functional Requirements
-   **Security:** Ensure `.gitignore` prevents snapshots from being committed.
-   **Efficiency:** Minimal overhead for disk I/O.
-   **Traceability:** Log when a file is served from cache vs. freshly fetched.

## Acceptance Criteria
-   A new `scraper/snapshots/` directory is created and correctly ignored by git.
-   Running the scraper with a course URL creates a local file.
-   Subsequent runs of the same URL use the local file and do not trigger a network request.
-   `FORCE_REFRESH` successfully updates the local file.
-   Integration tests for `UniversalEngine` can optionally use the snapshot directory.

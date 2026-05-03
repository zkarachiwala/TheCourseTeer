# Requirements: Visual Scraper Builder (POC)

## Category: Setup (SETUP)
- **SETUP-01**: Initialize Next.js App Router project in `web/` directory.
- **SETUP-02**: Configure Drizzle ORM with Supabase connection.
- **SETUP-03**: Ensure shared types between Python scraper and Next.js frontend (e.g., `scraper_configs` schema).

## Category: Loading & Proxying (LOAD)
- **LOAD-01**: Implement a server-side proxy in Next.js to bypass CORS when fetching university pages.
- **LOAD-02**: Integrate a managed headless browser service (e.g., Browserless.io) via WebSocket for reliable JS rendering.
- **LOAD-03**: Handle relative links and assets (CSS, Images) in the proxied page to ensure it renders correctly in the UI.

## Category: Visual Tagging (TAG)
- **TAG-01**: Create an interactive overlay (iframe or shadow DOM) that allows clicking on page elements.
- **TAG-02**: Highlight the hovered/selected element to provide visual feedback.
- **TAG-03**: Allow users to assign a "Tag" (e.g., `course_title`, `atar`, `duration`) to the selected element.
- **TAG-04**: Implement support for **repeating sections** (e.g., tagging a container for campuses and then tagging sub-elements within it).
- **TAG-05**: Implement an algorithm to generate a resilient CSS selector for the selected element.
- **TAG-06**: Support "Visual Anchor Logic" — if a direct selector is too brittle, allow pinning to a nearby text label (e.g., "Find the text 'ATAR' and take the next sibling").

## Category: Saving & Integration (SAVE)
- **SAVE-01**: Implement a UI for reviewing and editing generated selectors before saving.
- **SAVE-02**: Migrate/Unify `site_configs` and `scraper_configs` into a single consistent schema for both the Builder and the Python Scraper Engine.
- **SAVE-03**: Ensure the Python `UniversalEngine` can immediately consume the unified configuration without code changes.

## Category: Validation (VALIDATE)
- **VALIDATE-01**: Provide a "Test" button that runs the extraction logic against the loaded page using the generated selectors.
- **VALIDATE-02**: Display the extracted data in a "Preview" panel to verify accuracy.
- **VALIDATE-03**: Show a "Confidence Score" for each extracted field (based on the method used).

## Category: UI/UX (UI)
- **UI-01**: Side-by-side view: University page on the left, tagging controls/preview on the right.
- **UI-02**: List of required fields for a university scraper to ensure complete data collection.
- **UI-03**: Status indicators for saved/unsaved changes.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Pending |
| SETUP-02 | Phase 1 | Pending |
| SETUP-03 | Phase 1 | Pending |
| LOAD-01 | Phase 1 | Pending |
| LOAD-02 | Phase 1 | Pending |
| LOAD-03 | Phase 1 | Pending |
| TAG-01 | Phase 2 | Pending |
| TAG-02 | Phase 2 | Pending |
| TAG-03 | Phase 2 | Pending |
| TAG-04 | Phase 3 | Pending |
| TAG-05 | Phase 3 | Pending |
| TAG-06 | Phase 3 | Pending |
| SAVE-01 | Phase 3 | Pending |
| SAVE-02 | Phase 3 | Pending |
| SAVE-03 | Phase 3 | Pending |
| VALIDATE-01 | Phase 4 | Pending |
| VALIDATE-02 | Phase 4 | Pending |
| VALIDATE-03 | Phase 4 | Pending |
| UI-01 | Phase 1 | Pending |
| UI-02 | Phase 2 | Pending |
| UI-03 | Phase 3 | Pending |

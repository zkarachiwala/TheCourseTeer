# Implementation Plan: Visual Scraper Builder UI & Tagging

## Phase 1: Foundation & Scaffolding [checkpoint: n/a]
- [x] Task: Create admin route at `web/src/app/admin/scraper-builder/` [commit: n/a]
- [x] Task: Configure Drizzle schema for `scraper_configs` (if not already complete) [commit: n/a]
- [x] Task: Implement a basic CORS proxy route in Next.js API [commit: n/a]

## Phase 2: Page Loading & Display [checkpoint: n/a]
- [x] Task: Build the URL input component with basic validation [commit: n/a]
- [x] Task: Implement an iframe-based viewer that loads content via the CORS proxy [commit: n/a]
- [x] Task: Ensure external resources (CSS/images) load correctly through the proxy [commit: n/a]

## Phase 3: Interactive Selector [checkpoint: n/a]
- [x] Task: Develop an overlay script to detect element hovers and clicks within the iframe [commit: n/a]
- [x] Task: Implement visual highlighting (border/background) for the currently hovered element [commit: n/a]
- [x] Task: Create a modal or sidebar that opens on element click to assign a field tag [commit: n/a]

## Phase 4: Multi-Page Navigation & Context [checkpoint: n/a]
- [x] Task: Update `scraper_configs` schema/model to include `page_path` or `url_pattern` [commit: n/a]
- [x] Task: Intercept link clicks in the overlay script to keep navigation within the proxy [commit: n/a]
- [x] Task: Implement a "Page Context" UI to track multiple URLs in a single configuration set [commit: n/a]
- [~] Task: Add "Tagging Mode" toggle to switch between interacting and selecting
- [ ] Task: Implement "Back" navigation to return to previous pages in the mapping session

## Phase 5: Selector Generation Logic
- [~] Task: Implement logic to generate a CSS selector for a selected DOM node
- [ ] Task: Enhance selector generation to prioritize stable IDs and specific classes
- [ ] Task: Add support for generating XPath as an alternative/fallback

## Phase 6: Persistence & Integration
- [x] Task: Create a Server Action to save generated selectors to the `scraper_configs` table [commit: n/a]
- [~] Task: Implement an "AI Parsing Preview" to show how selected text maps to field requirements
- [ ] Task: Implement a "Test Selector" feature to verify extraction before saving
- [ ] Task: Build a list view of existing configurations for the current university

## Phase 7: Final Verification
- [ ] Task: Perform end-to-end testing with a live university course page (e.g., RMIT or Unimelb)
- [ ] Task: Verify that saved selectors are correctly retrieved and usable by the Python scraper
- [ ] Task: Conductor - User Manual Verification 'Visual Scraper Builder UI & Tagging' (Protocol in workflow.md)

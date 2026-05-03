# Roadmap: Visual Scraper Builder (POC)

## Phases

- [ ] **Phase 1: Setup & Proxy** - Establish the project foundation and a reliable way to load university pages into the UI.
- [ ] **Phase 2: Visual Tagging** - Enable users to select elements on the page and assign them to course data fields.
- [ ] **Phase 3: Selection Logic & Persistence** - Generate resilient selectors, support complex patterns, and save configurations to the database.
- [ ] **Phase 4: Validation & Testing** - Verify the accuracy of extracted data and provide feedback before finalizing a scraper.

## Phase Details

### Phase 1: Setup & Proxy
**Goal**: Establish the project foundation and a reliable way to load university pages into the UI.
**Depends on**: Nothing
**Requirements**: SETUP-01, SETUP-02, SETUP-03, LOAD-01, LOAD-02, LOAD-03, UI-01
**Success Criteria** (what must be TRUE):
  1. Next.js App Router project is initialized and connected to Supabase via Drizzle.
  2. A university URL can be entered into the UI and the page is rendered in an iframe/container.
  3. Proxied pages include all original styling and handle JavaScript execution via Playwright/Puppeteer.
  4. UI layout provides a clear side-by-side workspace (Page on left, Controls on right).
**Plans**: TBD
**UI hint**: yes

### Phase 2: Visual Tagging
**Goal**: Enable users to select elements on the page and assign them to course data fields.
**Depends on**: Phase 1
**Requirements**: TAG-01, TAG-02, TAG-03, UI-02
**Success Criteria** (what must be TRUE):
  1. Hovering over elements in the proxied page provides a visual highlight (border/background).
  2. Clicking an element captures its properties and opens a mapping dropdown.
  3. A checklist displays which required fields (e.g., Name, ATAR) have been mapped for the current session.
**Plans**: TBD
**UI hint**: yes

### Phase 3: Selection Logic & Persistence
**Goal**: Generate resilient selectors, support complex patterns, and save configurations to the database.
**Depends on**: Phase 2
**Requirements**: TAG-04, TAG-05, TAG-06, SAVE-01, SAVE-02, SAVE-03, UI-03
**Success Criteria** (what must be TRUE):
  1. The system automatically generates a CSS selector for each tagged element.
  2. Users can define repeating sections (e.g., campuses) and tag child elements within them.
  3. Users can use text anchors (e.g., "value near text 'ATAR'") to stabilize selectors.
  4. Scraper configurations are successfully written to the `scraper_configs` table in Supabase.
**Plans**: TBD
**UI hint**: yes

### Phase 4: Validation & Testing
**Goal**: Verify the accuracy of extracted data and provide feedback before finalizing a scraper.
**Depends on**: Phase 3
**Requirements**: VALIDATE-01, VALIDATE-02, VALIDATE-03
**Success Criteria** (what must be TRUE):
  1. A "Test Extraction" action runs the extraction logic against the live proxied page.
  2. A preview panel displays the resulting JSON data for verification.
  3. Confidence scores are displayed for each field based on selector specificity.
**Plans**: TBD
**UI hint**: yes

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Setup & Proxy | 0/1 | Not started | - |
| 2. Visual Tagging | 0/1 | Not started | - |
| 3. Selection Logic & Persistence | 0/1 | Not started | - |
| 4. Validation & Testing | 0/1 | Not started | - |

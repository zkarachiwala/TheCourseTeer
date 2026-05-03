# Project: The Courseteer - Visual Scraper Builder (POC)

## Core Value
Accelerate the expansion and maintenance of the Australian undergraduate course aggregator by providing a visual, no-code interface for defining and testing web scraper configurations.

## Target User
- **Scraper Developers:** Who need to quickly build new university scrapers.
- **Data Curators:** Who need to update broken selectors when university websites change.

## Constraints
- **Framework:** Next.js (App Router) for the web interface, Python for the scraper engine.
- **Database:** Supabase (PostgreSQL) is the source of truth for all configurations.
- **Hosting:** Azure Static Web Apps.
- **Data Scope:** Strictly undergraduate courses from Australian universities.
- **Legal:** Must respect `robots.txt` (checked by the engine).

## Success Criteria (High-Level)
- [ ] Users can load a live university course page within the app.
- [ ] Users can visually select elements (Title, ATAR, Fees, etc.) and map them to database fields.
- [ ] The app generates resilient CSS/XPath selectors and handles common web patterns (e.g., hidden elements, dynamic content).
- [ ] Generated configurations are saved directly to the `scraper_configs` table.
- [ ] Configurations can be immediately tested against the live page before saving.
- [ ] Integration with the existing `UniversalEngine` in Python is seamless.

# Specification: Visual Scraper Builder UI & Tagging

**Objective:** Implement an interactive web interface that allows users to load university course pages, visually select elements, and map them to database fields by generating CSS/XPath selectors.

**Components:**
1. **Next.js Dashboard:** A focused admin interface within the existing `web/` application.
2. **CORS Proxy:** A server-side utility to load external university pages while bypassing browser security restrictions.
3. **Interactive Overlay:** A JavaScript layer that injects into the loaded page to handle hover, click, and element highlighting.
4. **Selector Engine:** Logic to calculate the most resilient selector for a given DOM element.
5. **Data Persistence:** Integration with the `scraper_configs` table in PostgreSQL.

**Success Criteria:**
- User can input a URL and see the external page rendered.
- User can click an element on the rendered page and assign a tag (e.g., "Course Title").
- The system generates a valid selector that accurately identifies that element.
- The selector can be saved to the database and is usable by the Python scraper.

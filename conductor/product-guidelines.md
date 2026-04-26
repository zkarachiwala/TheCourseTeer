# Visual Scraper Builder (POC) Guidelines

**UX/UI Principles:**
- **Interactive Feedback:** Visual cues (highlighting, tooltips) when hovering and selecting page elements.
- **Side-by-Side View:** The target website should be displayed alongside the tagging controls.
- **Status Indicator:** Clear indication if a selector successfully finds data on the current page.

**Technical Constraints:**
- **CORS Handling:** The app must reliably load and interact with external university websites (likely requiring a proxy).
- **Selector Stability:** Prioritize robust attributes (e.g., IDs, specific classes) over fragile positional paths.
- **Scraper Format:** Selectors must be compatible with the Python `UniversalEngine`.
- **Scraper Integration:** Must update the `site_configs` table in the PostgreSQL database.
- **Visual Anchors:** The engine should favor text-based labels (e.g., "ATAR") as robust fallbacks when DOM structure changes.

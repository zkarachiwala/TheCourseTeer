# Initial Concept

The goal is to build an undergraduate course aggregator and search engine for Australian university courses. A core component of this is an automated scraper fleet that keeps course data (ATARs, fees, etc.) up-to-date. To scale this, we are building a "Visual Scraper Builder" that allows non-technical users to visually map website elements to data points, generating configurations for our centralized scraping engine.

# Universal Scraper Engine

**Objective:** Provide a resilient, configuration-driven engine for extracting course data from diverse university websites.

**Core Functionality:**
- **Config-Driven:** Scrapers are defined by JSON extraction maps (CSS selectors, regex, etc.) stored in the `site_configs` table.
- **Visual Anchor Logic:** A fallback mechanism that searches for text labels (e.g., "ATAR") when primary selectors fail.
- **Multi-Campus Support:** Handles courses offered across different locations, mapping them to standardized database IDs.
- **Follow-through Requests:** Ability to fetch auxiliary data from detail JSON endpoints or sub-pages.
- **Course Level Filtering:** Configurable filtering (via `COURSE_LEVEL_FILTER`) to focus strictly on undergraduate degrees.
- **Confidence Scoring:** Assigns audit scores (100/70/30) to each extraction based on the method used (Selector vs. Anchor vs. Default).

# Visual Scraper Builder (POC)

**Objective:** Accelerate the development of university course scrapers by providing a visual interface for mapping website elements to data points.

**Core Functionality:**
- **URL Preview:** Input a university course page URL to load it within the application.
- **Visual Tagging:** An interactive overlay that allows users to click on page elements (e.g., Course Title, ATAR, Fees) and assign them to specific database fields.
- **Selector Generation:** Automatically derive resilient CSS or XPath selectors for tagged elements.
- **Config Integration:** Save the generated selectors directly to the `site_configs` table for use by the Python `UniversalEngine`.
- **Validation:** Test the generated selectors against the live page to confirm accurate data extraction before saving.

**Target User:** Developers and data curators managing the Courseteer scraper fleet.

# Initial Concept

The goal is to build a POC of an app that, when given a sample university course URL, displays the website in an interactive interface. Users will be able to associate parts of the loaded page with tags identifying key data points (e.g., ATAR, course name, duration). The tool will then generate the corresponding scraper configurations (CSS/XPath selectors) to automate the data extraction process, significantly reducing the manual labor required to build scrapers for each university.

# Visual Scraper Builder (POC)

**Objective:** Accelerate the development of university course scrapers by providing a visual interface for mapping website elements to data points.

**Core Functionality:**
- **URL Preview:** Input a university course page URL to load it within the application.
- **Visual Tagging:** An interactive overlay that allows users to click on page elements (e.g., Course Title, ATAR, Fees) and assign them to specific database fields.
- **Selector Generation:** Automatically derive resilient CSS or XPath selectors for tagged elements.
- **Config Integration:** Save the generated selectors directly to the `scraper_configs` table for use by the Python scraper engine.
- **Validation:** Test the generated selectors against the live page to confirm accurate data extraction before saving.

**Target User:** Developers and data curators managing the Courseteer scraper fleet.

# Visual Scraper Builder (POC) Tech Stack

**Frontend/Backend Framework:**
- **Next.js (App Router, v14+):** Used for building the interactive UI and server-side logic.
- **TypeScript:** Ensuring type safety for data structures and components.
- **Tailwind CSS:** Responsive styling for the side-by-side view.

**Data & Infrastructure:**
- **PostgreSQL:** Primary database (Supabase in production).
- **Drizzle ORM:** Managing database operations and schema integration.
- **Next.js Server Actions:** Handling selector saving and database updates.

**Web Loading & Scraper Integration:**
- **Proxy/CORS Handler:** Node.js-based proxy to bypass CORS and load university sites within the UI.
- **Playwright (Python):** For simulating and validating generated selectors against live sites.
- **Selector Engine:** Logic to generate CSS and XPath selectors from user-selected elements.

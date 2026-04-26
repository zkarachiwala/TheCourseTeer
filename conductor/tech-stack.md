# Visual Scraper Builder (POC) Tech Stack

**Frontend/Backend Framework:**
- **Next.js (App Router, v14+):** Used for building the interactive UI and server-side logic.
- **TypeScript:** Ensuring type safety for data structures and components.
- **Tailwind CSS:** Responsive styling for the side-by-side view.

**Data & Infrastructure:**
- **PostgreSQL:** Primary database (Supabase in production).
- **Drizzle ORM:** Managing database operations and schema integration.
- **Next.js Server Actions:** Handling selector saving and database updates.

**Scraper Engine:**
- **Python 3.12+:** Core language for the scraper backend.
- **UniversalEngine:** Centralized, configuration-driven scraper class.
- **BeautifulSoup & HTTPX:** For high-performance static scraping.
- **Playwright (Python):** For dynamic rendering and Cloudflare bypass.
- **psycopg3:** For asynchronous database pooling and interaction.

**Web Loading & Proxying:**
- **Node.js Proxy:** For bypassing CORS when loading university sites in the UI.
- **Selector Engine:** Logic to generate resilient CSS/XPath selectors from user clicks.

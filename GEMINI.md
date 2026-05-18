# The Courseteer - An Australian undergraduate course aggregator and search engine

All project documentation is in the planning directory.

## Development Methodology

At present I am leveraging different commmand line-based AI tools to build the entire package.  I am using the following tools:

- Claude code to build the scraper application to scrape university websites for details as per the documentation
- The scraper app will farm out lesser tasks to other AI models including Google Gemini and Ollama
- Claude code to build the web app to display the scraped information as the core application

## iOS & App Icon Standards

- **Transparency:** iOS (apple-touch-icon) does NOT support transparency. Transparent areas default to solid black.
- **Backgrounds:** Always use a solid background color (e.g., white or brand primary) and flatten the alpha channel.
- **Format:** Icons should be square PNGs (180x180 standard, 600x600+ for high quality). iOS applies the rounded corner mask automatically.
- **Workflow:** When requested to generate or update iOS-related icons, proactively confirm the desired background color before implementation.

## What Gemini is used for

Gemini CLI handles well-specified, mechanical tasks that don't require full codebase context:

- Generating boilerplate: Next.js pages, API routes, Tailwind components
- Writing scraper extraction logic for a single university (given the HTML structure)
- Writing unit tests for a specified function or module
- Generating SQL migration files from a schema description
- Drafting config files (`.env.example`, CI yaml, `pyproject.toml`)

Invoke via: `gemini -m gemini-2.5-flash -p "<task>"`

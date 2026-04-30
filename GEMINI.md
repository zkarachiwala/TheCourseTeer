# The Courseteer - An Australian undergraduate course aggregator and search engine

All project documentation is in the planning directory.

## Development Methodology

At present I am leveraging different commmand line-based AI tools to build the entire package.  I am using the following tools:

- Claude code to build the scraper application to scrape university websites for details as per the documentation
- The scraper app will farm out lesser tasks to other AI models including Google Gemini and Ollama
- Claude code to build the web app to display the scraped information as the core application

## What do I need Google Gemini to focus on

The task of building the scraper is labourious.  So far we have built 3 scrapers and they need to go through rounds of validation and tweaking.

I was thinking there could be a better way.  Could we build a POC of an app that when given a sample URL it would display the website in the interface.
The user would be able to associate parts of the loaded in page to tags that identify key data points that need to be scraped.  This could short-cut the build of scrapers

This would work like an OCR tool but instead of just extracting text it would also extract the structure of the page and allow the user to identify key data points visually.  The app would then generate a scraper based on the identified data points and the structure of the page.

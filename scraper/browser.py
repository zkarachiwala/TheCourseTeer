from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import BrowserContext, async_playwright

from http_client import BROWSER_UA


@asynccontextmanager
async def browser_context(headless: bool = True) -> AsyncIterator[BrowserContext]:
    """
    Async context manager that yields a Playwright BrowserContext.

    One browser instance is created per context; create one context per
    university scrape run to avoid session bleed.

    Usage::

        async with browser_context() as ctx:
            page = await ctx.new_page()
            await page.goto(url)
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        ctx = await browser.new_context(user_agent=BROWSER_UA)
        try:
            yield ctx
        finally:
            await browser.close()

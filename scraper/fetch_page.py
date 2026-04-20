import asyncio
import sys
import random
from playwright.async_api import async_playwright

async def fetch_page(url):
    async with async_playwright() as p:
        # Launch with some common "stealth" flags
        browser = await p.chromium.launch(headless=True)
        
        # Use a more complete browser context
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale='en-AU',
            timezone_id='Australia/Melbourne'
        )
        
        page = await context.new_page()
        
        # Set extra headers to look more like a real browser
        await page.set_extra_http_headers({
            'Accept-Language': 'en-AU,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
        })
        
        try:
            # Navigate with a generous timeout
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait a bit longer for any post-load JS to settle
            await asyncio.sleep(2)
            
            # If it's a SPA or has lazy content, scroll a bit
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            
            # Get the fully rendered HTML
            content = await page.content()
            
            # Print to stdout
            sys.stdout.buffer.write(content.encode('utf-8'))
        except Exception as e:
            print(f"ERROR: {str(e)}", file=sys.stderr)
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_page.py <url>", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    asyncio.run(fetch_page(url))

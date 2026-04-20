"""Debug script: use page.evaluate() fetch to call Funnelback from within the browser."""
import asyncio
import json

from browser import browser_context

# Load this page first to get Cloudflare clearance for the funnelback domain
SEARCH_PAGE = "https://study.unimelb.edu.au/find?collection=uom%7Esp-courses&profile=_default&query=%21showall"
FUNNELBACK_URL = "https://uom-search.funnelback.squiz.cloud/s/search.json"


async def main():
    print("Loading search page to obtain Cloudflare clearance ...")
    async with browser_context() as ctx:
        page = await ctx.new_page()
        await page.goto(SEARCH_PAGE, wait_until="networkidle", timeout=60000)
        print("  Page loaded. Running in-browser fetch to Funnelback API ...")

        # Fire the API request from inside the browser — inherits CF clearance
        result = await page.evaluate("""async () => {
            const params = new URLSearchParams({
                'collection': 'uom~sp-courses',
                'profile': '_default',
                'query': '!showall',
                'num_ranks': '200',
                'start_rank': '1',
                'sort': 'metacourseDisplayTitle',
                'f.Study level|courseStudyLevel': 'undergraduate',
            });
            const url = 'https://uom-search.funnelback.squiz.cloud/s/search.json?' + params.toString();
            const resp = await fetch(url, {
                headers: { 'Referer': 'https://study.unimelb.edu.au/' }
            });
            return resp.json();
        }""")
        await page.close()

    print(f"\nTop-level keys: {list(result.keys())}")
    results_root = (
        result.get("response", {})
        .get("resultPacket", {})
        .get("results", [])
    )
    total = (
        result.get("response", {})
        .get("resultPacket", {})
        .get("resultsSummary", {})
        .get("totalMatching", "unknown")
    )
    print(f"Results returned: {len(results_root)}  Total matching: {total}")

    if results_root:
        print(f"\nFirst result keys: {list(results_root[0].keys())}")
        print(f"\nFirst result metadata:\n{json.dumps(results_root[0].get('listMetadata', {}), indent=2)[:1500]}")

    course_urls = []
    for r in results_root:
        url = r.get("liveUrl") or r.get("indexUrl") or ""
        if "/find/courses/undergraduate/" in url:
            course_urls.append(url)

    print(f"\nUG course URLs found: {len(course_urls)}")
    for u in sorted(course_urls):
        print(f"  {u}")


asyncio.run(main())

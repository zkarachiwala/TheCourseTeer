import asyncio
import re
import httpx

async def test():
    url = "https://www.swinburne.edu.au/course/sitemap.xml/"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        # Test original regex
        found = re.findall(r"<loc>(https?://[^<]+)</loc>", resp.text)
        print(f"Found with original regex: {len(found)}")
        if len(found) > 0:
            print(f"Example: {found[0]}")
            
        # Test more robust regex
        found2 = re.findall(r"<loc>\s*(https?://[^\s<]+)\s*</loc>", resp.text)
        print(f"Found with robust regex: {len(found2)}")
        
        # Test if it has undergraduate
        undergrad = [u for u in found if "/course/undergraduate/" in u]
        print(f"Undergraduate URLs: {len(undergrad)}")

if __name__ == "__main__":
    asyncio.run(test())

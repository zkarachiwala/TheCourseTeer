import asyncio
import json
import os
from datetime import datetime
from uuid import UUID

import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# University IDs (fetched previously)
UNI_MAP = {
    "rmit": "233ba035-fb1a-4016-b0e4-52fd0d6705e8",
    "monash": "d43861dd-c4ac-4c55-aa0b-f5337c15576f",
    "unimelb": "efd28617-ec88-42ca-a710-6b3edd5f8e0e",
    "latrobe": "f5b3d349-0214-480b-89bc-7b70298e722b",
    "swinburne": "fa7b5854-a3bd-4572-aff6-d43cf6249581",
}

SITE_CONFIGS = [
    {
        "university_id": UNI_MAP["rmit"],
        "base_url": "https://www.rmit.edu.au",
        "extraction_map": {
            "name": {"selector": "meta[name='product_name']", "attr": "content"},
            "duration": {"selector": "meta[name='duration_domestic']", "attr": "content", "anchor": "Duration"},
            "atar": {"selector": "meta[name='atar']", "attr": "content", "anchor": "ATAR"},
            "fees": {"selector": "meta[name='fees_domestic']", "attr": "content", "anchor": "Fees"},
            "location": {"selector": "meta[name='location_domestic']", "attr": "content", "anchor": "Location"},
            "admissions_codes": {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
        },
        "discovery_config": {
            "method": "sitemap",
            "url": "https://www.rmit.edu.au/sitemap.xml",
            "include_patterns": ["/study-with-us/levels-of-study/undergraduate-study/"]
        },
        "robots_txt_status": "allowed",
        "notes": "RMIT uses 'elastic' class meta tags for most data."
    },
    {
        "university_id": UNI_MAP["monash"],
        "base_url": "https://www.monash.edu",
        "extraction_map": {
            "name": {"selector": "h1", "json_ld": "Course.name"},
            "duration": {"selector": "table.course-page__table-basic tr", "key": "Duration", "anchor": "Duration"},
            "atar": {"selector": "div.course-page__subject-req-item", "anchor": "ATAR"},
            "fees": {"regex": r'"FeeDomesticCSP":\s*"A\$([0-9,]+)"', "anchor": "Fees"},
            "location": {"selector": "table.course-page__table-basic tr", "key": "Location", "anchor": "Location"},
            "admissions_codes": {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
        },
        "discovery_config": {
            "method": "regex_links",
            "url": "https://www.monash.edu/study/courses/find-a-course",
            "patterns": [r"https://www\.monash\.edu/study/courses/find-a-course/courses/[^\s\"<>&?]+-b\d{4}$"]
        },
        "robots_txt_status": "allowed",
        "notes": "Monash uses a mix of JSON-LD, tables, and regex on the data layer."
    },
    {
        "university_id": UNI_MAP["unimelb"],
        "base_url": "https://study.unimelb.edu.au",
        "extraction_map": {
            "name": {"selector": "h1"},
            "duration": {"anchor": "Duration", "regex": r"(\d+(?:\.\d+)?)"},
            "atar": {"anchor": "Guaranteed ATAR", "regex": r":\s*(\d{2}(?:\.\d+)?)"},
            "fees": {"anchor": "Commonwealth Supported Place"},
            "location": {"anchor": "Campus", "regex": r"(Parkville|Southbank|Online)"},
            "admissions_codes": {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
        },
        "discovery_config": {
            "method": "funnelback_api",
            "url": "https://uom-search.funnelback.squiz.cloud/s/search.json",
            "js_payload": "async () => { ... }"
        },
        "robots_txt_status": "allowed",
        "notes": "UniMelb relies heavily on visual anchors and Funnelback API metadata."
    },
    {
        "university_id": UNI_MAP["swinburne"],
        "base_url": "https://www.swinburne.edu.au",
        "extraction_map": {
            "name": {"selector": "h1"},
            "duration": {"selector": "div.course-details__duration", "anchor": "Duration"},
            "atar": {"selector": "div.course-fees__block", "anchor": "ATAR"},
            "fees": {"selector": "p.course-fees__total", "anchor": "Yearly fee"},
            "location": {"selector": "div.course-details__campus", "anchor": "Campus"},
            "admissions_codes": {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
        },
        "discovery_config": {
            "method": "sitemap",
            "url": "https://www.swinburne.edu.au/course/sitemap.xml",
            "include_patterns": ["/course/undergraduate/"]
        },
        "robots_txt_status": "allowed",
        "notes": "Swinburne uses dedicated detail divs and fee blocks."
    }
]

async def seed():
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            for config in SITE_CONFIGS:
                await cur.execute(
                    """
                    INSERT INTO site_configs (
                        university_id, base_url, extraction_map, robots_txt_status, notes, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (university_id) DO UPDATE SET
                        base_url = EXCLUDED.base_url,
                        extraction_map = EXCLUDED.extraction_map,
                        robots_txt_status = EXCLUDED.robots_txt_status,
                        notes = EXCLUDED.notes,
                        last_updated = EXCLUDED.last_updated
                    """,
                    (
                        config["university_id"],
                        config["base_url"],
                        json.dumps(config["extraction_map"]),
                        config["robots_txt_status"],
                        config["notes"],
                        datetime.now()
                    )
                )
            print(f"Seeded {len(SITE_CONFIGS)} site configurations.")

if __name__ == "__main__":
    asyncio.run(seed())

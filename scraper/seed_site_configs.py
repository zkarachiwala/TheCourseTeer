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
    "federation": "ea176745-a7d0-4773-b9dc-c08624754035",
    "vu": "76f950f6-4ff8-4a54-b3ad-f194221ece1c",
    "acu": "581b9252-ea48-45cb-9109-80fe634708ed",
}

# La Trobe Campus Codes to seed into external_code column
LATROBE_CAMPUS_CODES = [
    ("8841ca47-be65-4697-a49b-ed738259a315", "BU"), # Bundoora
    ("37a8e2ca-1643-48a5-85b1-6b91cc0bc15a", "BE"), # Bendigo
    ("074cbaa0-68fd-47fb-906e-6b99ed5fdcf0", "AW"), # Albury-Wodonga
    ("c97655c5-37de-4aaa-89da-923f264a1741", "SH"), # Shepparton
    ("cae2929f-5cda-4100-a542-85ae4ea327fb", "MI"), # Mildura
    ("b53c0416-8f3e-4a91-869d-f53d300cd8db", "MC"), # Melbourne City
    ("fa65309e-488e-4278-bc13-5e720e8a8b3d", "ON"), # Online
    # Fallback/Additional codes (multiple codes can map to same campus in seed script)
    ("8841ca47-be65-4697-a49b-ed738259a315", "Melbourne"), # Melbourne alias for Bundoora
    ("074cbaa0-68fd-47fb-906e-6b99ed5fdcf0", "WO"), # Wodonga
    ("b53c0416-8f3e-4a91-869d-f53d300cd8db", "CI"), # City
    ("b53c0416-8f3e-4a91-869d-f53d300cd8db", "SY"), # Sydney
    ("fa65309e-488e-4278-bc13-5e720e8a8b3d", "OT"), # Other
]

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
            "atar": {"anchor": "Guaranteed ATAR", "regex": r"(Guaranteed ATAR 2026: \d{2}(?:\.\d+)?)"},
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
            "location": {
                "selector": "div.course-details__campus", 
                "anchor": "Campus",
                "mapping": {
                    "Hawthorn": "682134ca-95e0-41be-8baa-3093db3c7ee5",
                    "Wantirna": "64308899-8c55-4cab-ba56-7fba2a57b57c",
                    "Croydon": "b7889aad-877d-432c-bc2b-0faf3b740c44",
                    "Prahran": "e0b1c3ed-63b3-4661-a203-f21d394e17f1",
                    "Online": "7aebbc4d-83c3-4418-91dd-30bc55a1a5ff"
                }
            },
            "admissions_codes": {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
        },
        "discovery_config": {
            "method": "sitemap",
            "url": "https://www.swinburne.edu.au/course/sitemap.xml/",
            "include_patterns": ["/course/undergraduate/"]
        },
        "robots_txt_status": "allowed",
        "notes": "Swinburne uses dedicated detail divs and fee blocks."
    },
    {
        "university_id": "f5b3d349-0214-480b-89bc-7b70298e722b", # La Trobe
        "base_url": "https://www.latrobe.edu.au",
        "extraction_map": {
            "name": {
                "selector": "h1.ds-course-header__title",
                "regex": r'"advertisedTitle"\s*:\s*"?([^",}]+)"?'
            },
            "duration": {
                "regex": r'"duration"\s*:\s*"([0-9.]+)"'
            },
            "atar": {
                "json_regex": r'"allAtars"\s*:\s*(\{.*?\})\s*,\s*"ugRse',
                "json_path": "latest_key"
            },
            "location": {
                "regex": r'"campuses"\s*:\s*(\[[^\]]+\])',
                "mapping": {
                    "BU": "8841ca47-be65-4697-a49b-ed738259a315", # Bundoora
                    "ON": "fa65309e-488e-4278-bc13-5e720e8a8b3d", # Online
                    "AW": "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0", # Albury-Wodonga
                    "WO": "074cbaa0-68fd-47fb-906e-6b99ed5fdcf0", # Wodonga -> Albury-Wodonga
                    "BE": "37a8e2ca-1643-48a5-85b1-6b91cc0bc15a", # Bendigo
                    "MC": "b53c0416-8f3e-4a91-869d-f53d300cd8db", # Melbourne City
                    "MI": "cae2929f-5cda-4100-a542-85ae4ea327fb", # Mildura
                    "SH": "c97655c5-37de-4aaa-89da-923f264a1741", # Shepparton
                    "SY": "b53c0416-8f3e-4a91-869d-f53d300cd8db", # Sydney -> Melbourne City
                    "OT": "fa65309e-488e-4278-bc13-5e720e8a8b3d", # Other -> Online fallback
                    "CI": "b53c0416-8f3e-4a91-869d-f53d300cd8db", # City -> Melbourne City
                }
            },
            "admissions_codes": {"regex": r'"vtacCode"\s*:\s*(\d{9,10})'},
            "follow_urls": {"regex": r"/courses/data/202[6-7]/domestic/[a-z]+/[^'\"\s]+"}
        },
        "discovery_config": {
            "method": "sitemap",
            "url": "https://www.latrobe.edu.au/sitemap.xml",
            "include_patterns": ["/courses/"]
        },
        "robots_txt_status": "allowed",
        "notes": "La Trobe discovery updated to prioritize main course pages for ATAR extraction. Uses follow_urls to find VTAC codes."
    },
    {
        "university_id": UNI_MAP["federation"],
        "base_url": "https://www.federation.edu.au",
        "extraction_map": {
            "name": {"selector": "title", "regex": r"^([^|]+?)\s*\|"},
            "duration": {"regex": r'"heading"\s*:\s*"Duration"\s*,\s*"summary"\s*:\s*"([^"]+)"'},
            "atar": {"regex": r'"heading"\s*:\s*"ATAR"\s*,\s*"summary"\s*:\s*"([^"]+)"'},
            "fees": {"regex": r'Commonwealth Supported Place'},
            "location": {
                "regex": r'"heading"\s*:\s*"Locations"\s*,\s*"summary"\s*:\s*"([^"]+)"',
                "mapping": {
                    "Ballarat":  "e84c817b-c88d-4211-801b-7f97009f0370",
                    "Mt Helen":  "e84c817b-c88d-4211-801b-7f97009f0370",
                    "Gippsland": "87036014-4081-4075-bbed-784bb926a788",
                    "Churchill": "87036014-4081-4075-bbed-784bb926a788",
                    "Berwick":   "c89c9c6b-4a6b-442e-801c-1073fa69b8fd",
                    "Online":    "e9649dc5-7636-4822-8d34-e192fc1bf195"
                }
            },
            "admissions_codes": {"regex": r"(37\d{8})"}
        },
        "discovery_config": {
            "method": "sitemap",
            "url": "https://www.federation.edu.au/sitemap.xml",
            "include_patterns": ["/courses/"]
        },
        "robots_txt_status": "allowed",
        "notes": "All course data in embedded JSON blob (Course essentials heading/summary pairs). Location uses <br> separators with delivery modes stripped by engine."
    }
]

async def seed():
    async with await psycopg.AsyncConnection.connect(DATABASE_URL, prepare_threshold=None) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET search_path = public")

            # Resolve VU Footscray Nicholson UUID (inserted by migration 20260503000002)
            await cur.execute("SELECT id FROM public.campuses WHERE slug = 'vu-footscray-nicholson'")
            row = await cur.fetchone()
            vu_footscray_nicholson_id = str(row[0]) if row else None

            vu_config = {
                "university_id": UNI_MAP["vu"],
                "base_url": "https://www.vu.edu.au",
                "extraction_map": {
                    "fetch_mode": "static",
                    "cleanup_regexes": [
                        r"<script[^>]*>.*?</script>",
                        r"<style[^>]*>.*?</style>",
                        r"\s*Applications closed",
                    ],
                    "name": {"selector": "h1"},
                    "duration": {
                        "anchor": "Duration",
                        "regex": r"(\d+(?:\.\d+)?)\s*years?"
                    },
                    "atar": {
                        "anchor": "Lowest selection rank",
                        "regex": r"(\d{2,3}(?:\.\d+)?)",
                        "log_missing": True
                    },
                    "fees": {"anchor": "Commonwealth supported place"},
                    "location": {
                        "anchor": "Location",
                        "mapping": {
                            "City Campus":                "3626dd07-e327-4322-aefd-c3c2023e53a4",
                            "Footscray Park Campus":      "1deddf26-ad7f-4dcd-a20a-beaf43ca219b",
                            "Footscray Park":             "1deddf26-ad7f-4dcd-a20a-beaf43ca219b",
                            "St Albans Campus":           "29c1b21e-0f5f-4ef2-865c-5c61773df451",
                            "St Albans":                  "29c1b21e-0f5f-4ef2-865c-5c61773df451",
                            "Online":                     "741bd14f-74cd-4a08-966d-5af35a391573",
                            "VU Online":                  "741bd14f-74cd-4a08-966d-5af35a391573",
                            "Online Real Time":           "741bd14f-74cd-4a08-966d-5af35a391573",
                            "Footscray Nicholson Campus": vu_footscray_nicholson_id,
                            "Footscray Nicholson":        vu_footscray_nicholson_id,
                            "Sunshine Campus":            "67530c6e-1691-4aed-b3f4-623a3bd95e3d",
                            "Sunshine":                   "67530c6e-1691-4aed-b3f4-623a3bd95e3d",
                        }
                    },
                    "admissions_codes": {
                        "anchor": "VTAC course code",
                        "regex": r"(43\d{8})"
                    },
                },
                "discovery_config": {
                    "method": "sitemap",
                    "url": "https://www.vu.edu.au/sitemap.xml?page=1",
                    "include_patterns": ["/courses/bachelor"]
                },
                "robots_txt_status": "allowed",
                "notes": (
                    "Nuxt SSR — static fetch works. ATAR = lowest selection rank only; "
                    "many courses have no ATAR (VU Block Model) — logged via log_missing flag. "
                    "VTAC codes in entry requirements section, 10-digit starting with 43. "
                    "Sydney/Brisbane campus strings silently dropped (not in mapping). "
                    "Crawl-delay 10 per robots.txt."
                ),
            }

            # Resolve ACU campus UUIDs (inserted by migration 20260503000001)
            await cur.execute("SELECT id FROM public.campuses WHERE slug = 'acu-melbourne'")
            row = await cur.fetchone()
            acu_melbourne_id = str(row[0]) if row else None

            await cur.execute("SELECT id FROM public.campuses WHERE slug = 'acu-ballarat'")
            row = await cur.fetchone()
            acu_ballarat_id = str(row[0]) if row else None

            await cur.execute("SELECT id FROM public.campuses WHERE slug = 'acu-online'")
            row = await cur.fetchone()
            acu_online_id = str(row[0]) if row else None

            acu_config = {
                "university_id": UNI_MAP["acu"],
                "base_url": "https://www.acu.edu.au",
                "extraction_map": {
                    "fetch_mode": "static",
                    "name": {
                        "selector": "meta[property='og:title']",
                        "attr": "content",
                        "regex": r"^(.+?)\s*\|\s*ACU courses?\s*$",
                    },
                    "duration": {
                        "regex": r"<dt>Duration</dt>\s*<dd>\s*(\d+(?:\.\d+)?)\s*years?",
                    },
                    "campus_array": {
                        "array_regex": r"const rendering_\w+ = (\[[\s\S]*?\]);",
                        "campus_title_key": "CampusTitle",
                        "atar_key": "ATARCode",
                        "atar_regex": r"(\d{2,3}(?:\.\d+)?)",
                        "tac_code_key": "TACCode",
                        "tac_label_key": "Code",
                        "vtac_filter": "VTAC code",
                        "mapping": {
                            "Melbourne":                    acu_melbourne_id,
                            "Ballarat":                     acu_ballarat_id,
                            "ACU Online Supported Program": acu_online_id,
                        },
                    },
                },
                "discovery_config": {
                    "method": "sitemap",
                    "url": "https://www.acu.edu.au/sitemap.xml",
                    "include_patterns": ["/course/bachelor"],
                },
                "robots_txt_status": "allowed",
                "notes": (
                    "Static HTML. Course name from og:title meta, '| ACU courses' suffix stripped. "
                    "Duration and fees from DT/DD anchor structure. "
                    "Campus data from inline JS array (const rendering_HASH). "
                    "Victorian campuses only: Melbourne (St Patrick's), Ballarat (Aquinas), Online. "
                    "Non-Victorian campuses (Brisbane, Canberra, North Sydney, Blacktown, Strathfield) "
                    "absent from campus_array.mapping — silently dropped. "
                    "VTAC codes are 10 digits starting with 12, extracted per campus from the JS array. "
                    "Courses with no Victorian campus are discarded (scrape_page returns None)."
                ),
            }

            # Seed Site Configs
            all_configs = SITE_CONFIGS + [vu_config, acu_config]
            for config in all_configs:
                # Merge discovery_config into extraction_map for storage
                full_map = config["extraction_map"].copy()
                if "discovery_config" in config:
                    full_map["discovery_config"] = config["discovery_config"]

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
                        json.dumps(full_map),
                        config["robots_txt_status"],
                        config["notes"],
                        datetime.now()
                    )
                )
            print(f"Seeded {len(all_configs)} site configurations.")

            # Seed Campus Aliases for La Trobe
            for campus_id, alias_code in LATROBE_CAMPUS_CODES:
                await cur.execute(
                    """
                    INSERT INTO campus_aliases (campus_id, alias_code)
                    VALUES (%s, %s)
                    ON CONFLICT (campus_id, alias_code) DO NOTHING
                    """,
                    (campus_id, alias_code)
                )
            print(f"Seeded {len(LATROBE_CAMPUS_CODES)} campus aliases for La Trobe.")

if __name__ == "__main__":
    asyncio.run(seed())

# University Scraping Registry

Status key: `mvp` = Phase 1 target | `phase2` = Phase 2 target | `tbd` = not yet assessed

Scraper mode key: `static` = httpx + BeautifulSoup (no browser) | `browser` = Playwright (JS rendering required)

Spike evidence for MVP universities: see [ROBOTS_SPIKE.md](ROBOTS_SPIKE.md).

---

## Phase 1 — MVP Universities

### 1. RMIT University
| Field | Value |
|---|---|
| Homepage | https://www.rmit.edu.au |
| Course URL pattern | `/study-with-us/levels-of-study/undergraduate-study/bachelor-degrees/[name]-[code]` |
| robots.txt blocks courses | No |
| Bot protection | None |
| Rendering | Server-rendered HTML |
| JSON-LD / Schema.org | None |
| ATAR in static HTML | Yes — `data-level` attributes |
| Fees in static HTML | Yes — `name="fees_domestic"` fields |
| Scraper mode | `static` |
| Course discovery | Sitemap at `/sitemap.xml` — enumerate all course slugs |
| Notes | Best case. All data in raw HTML. No Playwright needed. |
| Phase | `mvp` |

---

### 2. Monash University
| Field | Value |
|---|---|
| Homepage | https://www.monash.edu |
| Course URL pattern | `/study/courses/find-a-course/[name]-[code]` |
| robots.txt blocks courses | No |
| Bot protection | Cloudflare (resolved with browser User-Agent header) |
| Rendering | Server-rendered HTML |
| JSON-LD / Schema.org | Yes — `Course` type (name, description only) |
| ATAR in static HTML | Yes — 72 references in HTML |
| Fees in static HTML | Yes — inline JS data layer with exact CSP and DFEE amounts e.g. `"CSP": "A$14,500"`, `"FeeDomesticFullFee": "A$38,000"` |
| Scraper mode | `static` (browser UA header required) |
| Course discovery | Course listing pages + sitemap |
| Notes | Excellent data quality. Fee data as inline JSON object in `<script>` tag — parse with regex or JSON. Set `User-Agent` to browser string in httpx requests. |
| Phase | `mvp` |

---

### 3. University of Melbourne
| Field | Value |
|---|---|
| Homepage | https://www.unimelb.edu.au |
| Course URL pattern | `https://study.unimelb.edu.au/find/courses/undergraduate/[course-name]/` |
| robots.txt blocks courses | No |
| Bot protection | Cloudflare on both domains — Playwright required |
| Rendering | Nuxt.js SPA — all course data rendered client-side |
| JSON-LD / Schema.org | None |
| ATAR in static HTML | No — rendered by JS |
| Fees in static HTML | No — rendered by JS |
| Scraper mode | `browser` |
| Degree scope | UG only (MVP) |
| Course discovery | Parse `explore-courses-by-atar` listing page — server-rendered HTML (Squiz Matrix, not Nuxt). Course cards contain URLs, names, and ATAR data directly. ~25 unique UG courses total. |
| Campus | Parkville (primary), Southbank (arts/music). Courses at both flagged in `atar_issues` as `multiple_campuses`. Default to Parkville when no campus detected on page. |
| ATAR | Extracted from listing page course cards (guaranteed ATAR + lowest selection rank). Per-course pages used only for duration and campus confirmation. |
| Fees | All domestic UG are CSP (`csp_available=true`). `price_annual_csp_aud` deferred (fees tab pass not yet implemented). `price_annual_dfee_aud` null (no domestic full-fee UG places). |
| Faculty | Inferred from course name via keyword map (see `unimelb.py`). Reference: https://about.unimelb.edu.au/strategy/our-structure/faculties-and-graduate-schools |
| Phase | `mvp` |

---

## Phase 2 — All Remaining Australian Universities

Grouped by expected scraper complexity based on typical university web stack patterns. All require individual robots.txt verification and a scraping spike before implementation.

### Group A — Likely static HTML (lower effort)
These universities typically use standard CMS platforms (Adobe Experience Manager, Squiz Matrix, WordPress) with server-rendered course pages.

| University | Homepage | Phase | Status |
|---|---|---|---|
| University of Adelaide | https://www.adelaide.edu.au | `phase2` | `tbd` |
| University of Western Australia | https://www.uwa.edu.au | `phase2` | `tbd` |
| University of Newcastle | https://www.newcastle.edu.au | `phase2` | `tbd` |
| University of Wollongong | https://www.uow.edu.au | `phase2` | `tbd` |
| Flinders University | https://www.flinders.edu.au | `phase2` | `tbd` |
| La Trobe University | https://www.latrobe.edu.au | `phase2` | `tbd` |
| Deakin University | https://www.deakin.edu.au | `phase2` | `tbd` |
| Curtin University | https://www.curtin.edu.au | `phase2` | `tbd` |
| Macquarie University | https://www.mq.edu.au | `phase2` | `tbd` |
| University of Tasmania | https://www.utas.edu.au | `phase2` | `tbd` |
| Griffith University | https://www.griffith.edu.au | `phase2` | `tbd` |
| James Cook University | https://www.jcu.edu.au | `phase2` | `tbd` |
| University of South Australia | https://www.unisa.edu.au | `phase2` | `tbd` |
| Charles Darwin University | https://www.cdu.edu.au | `phase2` | `tbd` |

### Group B — Likely browser required (moderate effort)
Newer sites or known React/Vue/Angular frontends.

| University | Homepage | Phase | Status |
|---|---|---|---|
| Australian National University | https://www.anu.edu.au | `phase2` | `tbd` |
| University of Technology Sydney | https://www.uts.edu.au | `phase2` | `tbd` |
| University of New South Wales | https://www.unsw.edu.au | `phase2` | `tbd` |
| Swinburne University | https://www.swinburne.edu.au | `phase2` | `tbd` |
| Bond University | https://bond.edu.au | `phase2` | `tbd` |
| Western Sydney University | https://www.westernsydney.edu.au | `phase2` | `tbd` |
| University of Canberra | https://www.canberra.edu.au | `phase2` | `tbd` |
| Queensland University of Technology | https://www.qut.edu.au | `phase2` | `tbd` |
| Victoria University | https://www.vu.edu.au | `phase2` | `tbd` |
| Murdoch University | https://www.murdoch.edu.au | `phase2` | `tbd` |

### Group C — Unknown / smaller institutions (assessment needed)
| University | Homepage | Phase | Status |
|---|---|---|---|
| Charles Sturt University | https://www.csu.edu.au | `phase2` | `tbd` |
| Federation University | https://federation.edu.au | `phase2` | `tbd` |
| Southern Cross University | https://www.scu.edu.au | `phase2` | `tbd` |
| Central Queensland University | https://www.cqu.edu.au | `phase2` | `tbd` |
| University of the Sunshine Coast | https://www.usc.edu.au | `phase2` | `tbd` |
| Edith Cowan University | https://www.ecu.edu.au | `phase2` | `tbd` |
| University of New England | https://www.une.edu.au | `phase2` | `tbd` |
| Torrens University | https://www.torrens.edu.au | `phase2` | `tbd` |
| Australian Catholic University | https://www.acu.edu.au | `phase2` | `tbd` |

---

## How to Add a New University

When spiking a new university for Phase 2, record the following in this file:

1. Fetch `robots.txt` — confirm course pages are not blocked
2. Load a sample course page with curl (browser UA) — check for JSON-LD, ATAR, fees in static HTML
3. Check if JS rendering is required (look for `__NEXT_DATA__`, `window.__NUXT__`, React root)
4. Confirm course URL pattern from sitemap or course listing page
5. Set `scraper mode` to `static` or `browser`
6. Update status from `tbd` to the confirmed approach

# Handoff: Courseteer Redesign

## Overview
A full high-fidelity redesign of The Courseteer — an Australian undergraduate course aggregator (currently Victorian universities). This handoff covers the courses listing page and a new course detail slide-over panel. A second variation (v2) adds monetisation features: sponsored listings, a featured university banner, and a shortlist with email lead capture.

## About the Design Files
The `.html` files in this folder are **design references built in HTML/React** — they are prototypes demonstrating intended look, behaviour, and interactions. They are **not production code to copy directly**.

Your task is to **recreate these designs inside the existing Next.js/Tailwind codebase** (`src/` folder), using its established patterns (server components, Drizzle ORM, Next.js App Router). The design files exist purely as a visual and behavioural reference.

## Fidelity
**High-fidelity.** These are pixel-accurate mockups with final colours, typography, spacing, and interactions. Recreate them as closely as possible using the existing codebase's conventions.

---

## Design Files
| File | Description |
|------|-------------|
| `Courseteer v1 (reference).html` | Clean redesign — no monetisation |
| `Courseteer v2 - Monetised (reference).html` | v1 + sponsored listings + featured uni banner + shortlist drawer |

Open these files in a browser to interact with the full prototype.

---

## Design Tokens

### Typography
| Token | Value |
|-------|-------|
| Display / Headings | `Manrope`, 700–800 weight |
| Body / UI | `Open Sans`, 400–600 weight |
| Google Fonts import | `Manrope:wght@300;400;500;600;700;800` + `Open+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400` |

### Colour — Dark Theme
| Token | Value |
|-------|-------|
| `--bg` | `oklch(10% 0.012 270)` |
| `--bg2` | `oklch(14% 0.012 270)` |
| `--bg3` | `oklch(18% 0.012 270)` |
| `--border` | `oklch(25% 0.012 270)` |
| `--text` | `oklch(98% 0 0)` |
| `--text2` | `oklch(72% 0.006 270)` |
| `--text3` | `oklch(52% 0.008 270)` |
| `--accent` | `oklch(85% 0.22 135)` (electric lime) |
| `--accent-fg` | `oklch(12% 0.05 135)` |
| `--accent-soft` | `oklch(85% 0.22 135 / 0.12)` |
| `--card-bg` | `oklch(16% 0.012 270)` |
| `--card-hover` | `oklch(20% 0.014 270)` |

### Colour — Light Theme
| Token | Value |
|-------|-------|
| `--bg` | `oklch(98% 0.006 90)` (warm white) |
| `--bg2` | `oklch(95% 0.008 90)` |
| `--bg3` | `oklch(92% 0.008 90)` |
| `--border` | `oklch(88% 0.008 90)` |
| `--text` | `oklch(12% 0.01 270)` |
| `--text2` | `oklch(45% 0.01 270)` |
| `--text3` | `oklch(65% 0.01 270)` |
| `--accent` | `oklch(58% 0.22 25)` (coral) |
| `--accent-fg` | `oklch(98% 0.005 90)` |
| `--accent-soft` | `oklch(58% 0.22 25 / 0.1)` |
| `--card-bg` | `oklch(100% 0 0)` |
| `--card-hover` | `oklch(98% 0.006 90)` |

> Recommendation: add these as CSS custom properties to `src/app/globals.css`, scoped under `.dark` and `:root` (or `html[class=light]`) to align with the existing `ThemeProvider` which uses the `class` attribute strategy.

### Spacing & Shape
| Property | Value |
|----------|-------|
| Card border radius | `16px` |
| Button border radius | `8–12px` |
| Badge border radius | `99px` (pill) |
| Panel border radius | `0` (full-height slide-over) |
| Header height | `60px` |
| Max content width | `1280px` |
| Content padding (sides) | `24px` |

### Shadows
| Token | Value |
|-------|-------|
| `--shadow` | `0 4px 24px oklch(0% 0 0 / 0.4)` (dark) / `0 2px 16px oklch(12% 0.01 270 / 0.08)` (light) |
| `--shadow-lg` | `0 12px 48px oklch(0% 0 0 / 0.6)` (dark) / `0 8px 40px oklch(12% 0.01 270 / 0.15)` (light) |

---

## Screens / Views

### 1. Header (`src/components/header.tsx`)
**Changes from current:**
- Sticky, `backdrop-filter: blur(20px)` with semi-transparent background
- Logo: small `30×30px` rounded square accent-colour badge with compass SVG icon + "The Courseteer" in Manrope 20px
- Nav: "Courses" shown as an active pill (`background: accent-soft`, `color: accent`)
- Theme toggle button: `36×36px` square, `border-radius: 8px`, shows ☀️/🌙 emoji
- **(v2 only)** Shortlist button: shows 📋 + "Shortlist" + badge count. Uses `accent-soft` background and `accent` border when count > 0.

### 2. Hero Section (`src/app/courses/page.tsx` or new `HeroSection` component)
**Layout:** Full-width, `padding: 60px 24px 52px`. Uses `--hero-gradient` background. Decorative blurred radial-gradient circles (purely CSS, `pointer-events: none`).

**Content:**
- Eyebrow label: `"Victorian Universities · Undergraduate"` — `12px`, `600` weight, `letter-spacing: 0.12em`, uppercase, `color: accent`
- H1: `"Find your path in [cycling word]"` — Manrope, `clamp(36px, 6vw, 68px)`, `line-height: 1.1`, `letter-spacing: -0.02em`
- Cycling word: rotates every 2s through: Engineering, Medicine, Law, Design, Business, Science, Arts, Nursing, Teaching, Technology. Animates out (fade + translateY(-8px)) then new word fades in.
- Fade-up entrance animation on load (0.7s, cubic-bezier(0.22,1,0.36,1))

**Search bar:**
- Full-width text input, `max-width: 500px`, `padding: 14px 16px 14px 44px` (left icon), `border-radius: 14px`, glass background (`oklch(100% 0 0 / 0.07)` dark / `oklch(100% 0 0 / 0.7)` light), border turns `accent` on focus
- University `<select>`, Duration `<select>`, Min ATAR `<input type="number">` — each `border-radius: 12px`, `padding: 13px`, custom chevron via `background-image` SVG, turns `accent` colour when a value is selected
- Active filter pills: `background: accent`, `color: accent-fg`, `border-radius: 99px`, `font-size: 12px`, animate in with `scaleIn`
- "Clear all" text button to reset all filters

**Implementation note:** The search/filter controls should be a `"use client"` component wrapping the existing `FilterRow` pattern. The hero H1 cycling animation is purely CSS/JS — no server involvement.

### 3. Listing Area Toolbar (`src/app/courses/page.tsx`)
- Result count: `"X courses found"` — 13px, `color: text3`
- Layout toggle: 3 buttons (⊞ Grid / ☰ List / ≡ Compact) in a pill container (`background: bg2`, `border: 1px solid border`, `border-radius: 10px`, `padding: 4px`). Active state: `background: accent`, `color: accent-fg`.

### 4. Course Card — Grid Layout
**Component:** New `CourseCard` component.

**Layout:** Flex column, `gap: 10px`, `padding: 22px 22px 16px`, `border-radius: 16px`, `background: card-bg`.

**Hover state:** `translateY(-3px) scale(1.01)`, border turns `accent`, `box-shadow: shadow-lg`. Transition: `0.2s cubic-bezier(0.34, 1.56, 0.64, 1)` (slight spring overshoot).

**Load animation:** `fadeUp` staggered by index (`animation-delay: idx * 40ms`).

**Content (top to bottom):**
1. Area badge (coloured pill — see area colour map below) + ATAR score (top right, colour-coded)
2. Course name — Manrope 18px, 700 weight
3. University short name — Open Sans 13px, `color: text2`, 500 weight
4. Divider (`border-top: 1px solid border`)
5. Campus (📍 icon) + Duration — 12px, `color: text3`
6. **(v2 only)** "+ Shortlist" / "✓ Shortlisted" toggle button — full width, `border-radius: 8px`, `padding: 7px`

**(v2 only) Sponsored treatment:**
- Corner ribbon: `"SPONSORED"` — `position: absolute`, top-right, `background: accent`, `color: accent-fg`, `font-size: 9px`, `padding: 3px 10px`, `border-bottom-left-radius: 8px`
- Border: `oklch(85% 0.22 135 / 0.35)` (lime tint)
- Sponsored courses sort to the top of results

#### Area Badge Colour Map
```
Science:     #6366f1 (indigo)
Business:    #0ea5e9 (sky)
Engineering: #f97316 (orange)
Technology:  #8b5cf6 (violet)
Design:      #ec4899 (pink)
Arts:        #14b8a6 (teal)
Medicine:    #ef4444 (red)
Law:         #a16207 (amber-dark)
Health:      #22c55e (green)
Education:   #06b6d4 (cyan)
Sport:       #84cc16 (lime)
```
Background: `{color}22`, text: `{color}`, `font-size: 11px`, `font-weight: 600`, `letter-spacing: 0.03em`, `border-radius: 99px`, `padding: 2px 8px`.

#### ATAR Colour Scale
```
≥ 95: #ef4444 (red — highly competitive)
≥ 85: #f97316 (orange)
≥ 75: #eab308 (yellow)
< 75: #22c55e (green — more accessible)
```

### 5. Course Row — List Layout
**Layout:** CSS Grid, `grid-template-columns: 1fr auto`, `padding: 16px 20px`, `border-bottom: 1px solid border`.

**Left:** University monogram badge (40×40px, `border-radius: 10px`, uni brand colour bg at 22% opacity) + course name (Manrope 16px) + meta row (uni short · campus · area badge).

**Right:** ATAR (colour-coded, 13px bold) + duration + "→" arrow (fades in on hover).

**Hover:** `background: card-hover`, arrow appears.

### 6. Course Row — Compact Table Layout
Standard `<table>` with columns: Course | University | Field | ATAR | Campus | Duration.

Header row: `background: bg2`, `font-size: 11px`, `font-weight: 700`, `text-transform: uppercase`, `letter-spacing: 0.06em`, `color: text3`.

Body rows: hover `background: card-hover`. University shown as monogram badge + short name.

### 7. Course Detail Panel (new component: `src/components/course-detail-panel.tsx`)
**Trigger:** Click any course card/row.

**Animation:** Slides in from right (`translateX(100%)` → `translateX(0)`), `0.3s cubic-bezier(0.16,1,0.3,1)`. Backdrop: `background: oklch(0% 0 0 / 0.5)`, `backdrop-filter: blur(4px)`, closes on click.

**Width:** `min(480px, 100vw)`. Keyboard: `Escape` closes.

**Layout (flex column, full height):**

**Header** (`padding: 24px 28px 20px`, border-bottom):
- Area badge
- Course name — Manrope 26px
- University name — 14px, `color: text2`
- Close button: `32×32px` circle, top-right

**Body** (scrollable, `padding: 24px 28px`):
- Stats grid (3 columns): ATAR / Duration / Campus — each in a `bg3` rounded card (`border-radius: 12px`, `padding: 14px 16px`). Label 11px uppercase, value 20px bold colour-coded, sub-label 10px.
- "About" section: description text, 15px, `line-height: 1.7`, `color: text2`
- University strip: monogram badge + full name + campus — `bg3`, `border-radius: 12px`

**Footer** (`padding: 20px 28px`, border-top):
- Primary CTA: "View on university website →" — full width, `background: accent`, `color: accent-fg`, `border-radius: 10px`, `padding: 13px`, 15px 600 weight. Links to `course.sourceUrl`.
- **(v2)** Secondary: "Save to shortlist" / "✓ Saved to shortlist" toggle — full width, `border: 1px solid border/accent`, changes to `accent-soft` background when saved.

**Implementation note:** This should be a `"use client"` component. State for open/closed lives in the courses page client wrapper. The `course.sourceUrl` already exists in the DB schema — use that for the CTA link.

---

## v2 — Monetisation Features

### 8. Featured University Banner (`src/components/featured-uni-banner.tsx`)
Sits between the hero and the listing toolbar.

**Layout:** Full-width within `max-width: 1280px` container, `padding: 16px 24px 0`.

**Card:** `border-radius: 16px`, gradient background from university brand colour at 18% opacity to `bg`, `border: 1px solid {uniColor}44` (thickens on hover). Flex row, space-between, wraps on mobile.

**Content:**
- Left: Uni monogram badge (48×48px) + name + "Sponsored" pill badge + tagline + highlight stats
- Right: CTA button in university brand colour

**Data model:** Add a `featuredUniversity` config (could be a DB table or env-driven flag) with: `uniId`, `tagline`, `highlight`, `ctaText`, `ctaUrl`.

### 9. Shortlist Feature

**DB/Storage:** Use `localStorage` key `courseteer_shortlist` (JSON array of course objects). For a logged-in future, migrate to a user table.

**Header badge:** When shortlist count > 0, show count bubble on the Shortlist button (`background: accent`, `color: accent-fg`, `18×18px` circle, `font-size: 11px`).

**Shortlist Drawer** (`src/components/shortlist-drawer.tsx`):
- Same slide-in panel pattern as course detail
- Lists saved courses with monogram + name + meta + remove (×) button
- Empty state: clipboard emoji + "No courses saved yet"
- **Email capture form** at bottom (`background: bg3`):
  - Label: "Get your shortlist emailed to you"
  - Sub-copy: "We'll also send ATAR updates and application deadlines for your saved courses."
  - Email input + "Send →" button (accent colour)
  - Fine print: "No spam. Unsubscribe anytime. Universities may reach out with relevant offers."
  - On submit: success state with 🎉 + confirmation message

**API endpoint to create:** `POST /api/shortlist` — accepts `{ email, courseIds[] }`, saves to a leads table (university partners pay per lead).

### 10. Sponsored Listings

**DB schema change:** Add to `courses` table:
```sql
sponsored       boolean  NOT NULL DEFAULT false,
sponsored_rank  integer  -- lower = higher placement
```

**Query change** in `getCourses()`: `ORDER BY sponsored DESC, sponsored_rank ASC NULLS LAST, {sort_col}`.

**Visual treatment:** `CourseCard` / `CourseRow` check `course.sponsored` and apply the ribbon + tinted border as described above.

---

## Animations Reference

```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes slideInPanel {
  from { transform: translateX(100%); }
  to   { transform: translateX(0); }
}
@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to   { transform: scale(1);    opacity: 1; }
}
```

Card stagger: `animation: fadeUp 0.4s calc(var(--idx) * 40ms) both ease` — pass index as a CSS variable or inline style.

---

## Files to Create / Modify

| Action | File | Notes |
|--------|------|-------|
| Modify | `src/app/globals.css` | Add CSS custom property theme tokens |
| Modify | `src/components/header.tsx` | New sticky blurred header, shortlist button (v2) |
| Modify | `src/app/courses/page.tsx` | Replace table with card/list/compact layouts; add hero section |
| Modify | `src/components/course-filter-row.tsx` | Restyle filters to match new pill/select design |
| Create | `src/components/course-card.tsx` | Grid card component |
| Create | `src/components/course-row.tsx` | List row component |
| Create | `src/components/course-detail-panel.tsx` | Slide-over detail panel |
| Create | `src/components/featured-uni-banner.tsx` | (v2) Sponsored university strip |
| Create | `src/components/shortlist-drawer.tsx` | (v2) Shortlist slide-over with email capture |
| Create | `src/app/api/shortlist/route.ts` | (v2) Lead capture API endpoint |
| Modify | `db/schema.ts` | (v2) Add `sponsored`, `sponsored_rank` to courses table |

---

## Assets
No external images required. All university branding uses initials-based monogram badges generated in CSS. Icons use emoji (📍, 📋, ☀️, 🌙) — replace with your preferred icon library if desired.

---

## Notes for the Developer
- The prototype uses inline React/Babel for rapid prototyping. **Do not copy the script tags** — use your existing Next.js component architecture.
- The `ThemeProvider` in `src/components/theme-provider.tsx` already handles dark/light via the `class` attribute on `<html>` — the CSS token system in this design plugs straight into that.
- The existing `FilterRow` is a `"use client"` component using `useRouter` — keep that pattern; just restyle it.
- The course detail panel requires a client-side state wrapper around the server-rendered course list. Pattern: server component fetches data and passes to a `CourseListClient` wrapper that manages selected course state.

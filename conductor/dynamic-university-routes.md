# Dynamic University Routes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement university-specific course listing pages at `/courses/[slug]` with top-level redirects (e.g., `/latrobe` -> `/courses/latrobe`).

**Architecture:** Use Next.js dynamic routes to capture the university slug, fetch university metadata and its specific courses in a Server Component, and pass them to an enhanced `CourseListClient` that handles pre-filtering.

**Tech Stack:** Next.js (App Router), Drizzle ORM, Postgres, React, TypeScript.

---

### Task 1: Enhance `CourseListClient` for Pre-filtering

**Files:**
- Modify: `web/src/components/course-list-client.tsx`

- [x] **Step 1: Add `initialUnis` prop to `CourseListClient`**
  Modify the `Props` interface and the component signature.

- [x] **Step 2: Initialize `selectedUnis` state with `initialUnis`**
  Update the `useState` hook.

- [x] **Step 3: Update `clearAll` to respect `initialUnis` (Optional or keep simple)**
  For now, let `clearAll` clear everything to allow users to "exit" the university-specific view if they want to browse others.

---

### Task 2: Create the Dynamic University Route

**Files:**
- Create: `web/src/app/courses/[slug]/page.tsx`

- [x] **Step 1: Implement the dynamic page component**
  This page will look very similar to `web/src/app/courses/page.tsx` but filtered by university slug.

---

### Task 3: Setup Top-Level Redirects

**Files:**
- Modify: `web/next.config.mjs`

- [ ] **Step 1: Add redirects to `next.config.mjs`**
  Since universities are dynamic, we could theoretically fetch them for redirects, but Next.js redirects are usually static. We can start with a manual list or just focus on `/latrobe` as requested.

---

### Task 4: Verification

- [ ] **Step 1: Verify `/courses/latrobe`**
  Manually visit the URL and check if only La Trobe courses appear and the banner is visible.

- [ ] **Step 2: Verify `/latrobe` redirect**
  Manually visit `/latrobe` and check if it redirects correctly.

- [ ] **Step 3: Verify 404 for invalid slug**
  Visit `/courses/invalid-university` and confirm it shows the Next.js 404 page.
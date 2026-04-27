# TASK: Implement Hybrid Public/Private Security Model

## Context
* **Target Apps:** University Course Aggregator & MobileHub PWA.
* **Infrastructure:** Azure Static Web Apps (Free Tier), Python API, Supabase.
* **Objective:** Allow public viewing of the UI/Portfolio but protect the API and Data from automated scraping, bots, and excessive bandwidth consumption.

## 1. Routing Configuration (staticwebapp.config.json)
Configure the application to allow anonymous access to static assets while gating the API:
* **Public Routes:** Allow `anonymous` access to `/`, `/index.html`, and `/assets/*`.
* **Protected Routes:** Restrict all `/api/*` endpoints to `authenticated` users only.
* **Auth Shortcuts:** Map `/login` to `/.auth/login/github` and `/logout` to `/.auth/logout`.
* **Fallback:** Set `navigationFallback` to `index.html` to support SPA routing.
* **Global Headers:** Implement `X-Content-Type-Options: nosniff` and a `Content-Security-Policy` that allows connections to Supabase.

## 2. Bot Deterrence (robots.txt)
Generate a `robots.txt` file in the public root directory with the following rules:
* **Delay:** Set a `Crawl-delay: 10` for standard engines.
* **AI Block:** Explicitly `Disallow` the following User-agents: `GPTBot`, `CCBot`, `ChatGPT-User`.
* **Scrape Protection:** Disallow crawling of the `/api/` and `/.auth/` directories.

## 3. Frontend Logic Update
Update the PWA entry point to handle the gated experience:
* **Auth Check:** Fetch from `/.auth/me` on application mount.
* **Conditional UI:** - If `clientPrincipal` is null: Display a "ReadOnly / Demo Mode" banner with a GitHub Login button.
    - If `clientPrincipal` exists: Enable full fetch functionality for course data/asset management.
* **Graceful Failure:** Ensure API `401` responses trigger a user-friendly notification rather than a console crash.

## 4. Verification (WSL/SWA CLI)
* Validate the config using `swa start`.
* Confirm that hitting an API endpoint while unauthenticated returns a `302` redirect or `401` status.
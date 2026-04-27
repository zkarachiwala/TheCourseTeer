# TASK: Implement Hybrid Public/Private Security Model

## Context
* **Target Apps:** University Course Aggregator & MobileHub PWA.
* **Infrastructure:** Azure Static Web Apps (Free Tier), Python API, Supabase.
* **Objective:** Allow public viewing of the UI/Portfolio but protect the API and Data from automated scraping, bots, and excessive bandwidth consumption.

## 1. Routing Configuration (staticwebapp.config.json)
Configure the application to allow anonymous access to static assets while gating the API and Admin routes:
* **Public Routes:** Allow `anonymous` access to the root (`/`), static assets, and `_next` files.
* **Protected Routes:** Restrict all `/api/*` and `/admin/*` endpoints to `authenticated` users only.
* **Auth Shortcuts:** 
    - `/login/github` -> `/.auth/login/github`
    - `/login/microsoft` -> `/.auth/login/aad`
    - `/logout` -> `/.auth/logout`
* **Response Overrides:** Redirect `401` unauthorized responses to the `/login` portal.
* **Global Headers:** Implement `X-Content-Type-Options: nosniff` and a `Content-Security-Policy` that allows connections to required backends (e.g., Supabase).

## 2. Bot Deterrence (robots.txt)
Generate a `robots.txt` file in the public root directory with the following rules:
* **Delay:** Set a `Crawl-delay: 10` for standard engines.
* **AI Block:** Explicitly `Disallow` the following User-agents: `GPTBot`, `CCBot`, `ChatGPT-User`.
* **Scrape Protection:** Disallow crawling of the `/api/`, `/admin/`, and `/.auth/` directories.

## 3. Frontend Logic Update
Update the application entry point to handle the gated experience:
* **Auth Check:** Fetch from `/.auth/me` on application mount to retrieve the `clientPrincipal`.
* **Conditional UI:** 
    - **Anonymous State:** Display a "ReadOnly / Demo Mode" banner with clear Sign-In options for GitHub and Microsoft.
    - **Authenticated State:** Enable full functionality and display user profile details/logout in the navigation.
* **Graceful Failure:** Ensure API `401` responses (e.g., from expired sessions) trigger a user-friendly notification or redirect rather than a silent failure.

## 4. Verification (Azure SWA CLI)
* Validate the config using `swa start`.
* Confirm that public routes (e.g., `/courses`) are accessible without login.
* Confirm that hitting a protected endpoint (e.g., `/api/data`) while unauthenticated returns a `302` redirect or `401` status.

# Specification: Undergraduate Course Filter & Supabase Configuration

## Objective
Ensure the application only processes undergraduate courses via a configurable filter and strictly document the use of Supabase for the database, even for local development.

## 1. Configurable Course Filter
- Add a new environment variable `COURSE_LEVEL_FILTER` with a default value of `UG` in `.env.example` and `web/.env.local.example`.
- Update `scraper/universal_engine.py`:
  - `_is_valid_course`: Read the environment variable. If `COURSE_LEVEL_FILTER` is `UG`, explicitly discard any courses starting with "master", "doctor", "juris doctor", "graduate certificate", or "graduate diploma".
  - `_infer_degree_type`: Keep returning `PG` for postgraduate courses, allowing `_is_valid_course` to act as the gatekeeper.
- Update `scraper/ai_parse.py`:
  - Modify the system prompt to instruct the AI to only extract undergraduate courses when `COURSE_LEVEL_FILTER=UG` or when the default is applied.

## 2. Supabase Database Enforcement
- `docker-compose.yml`: Leave the local Postgres setup intact for historical and local testing use cases.
- `.env.example` & `web/.env.local.example`: Update `DATABASE_URL` to explicitly use a Supabase connection string template (`postgresql://postgres.[project_ref]:[password]@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require`).
- `README.md`:
  - Update all references of course scope to "Australian undergraduate course aggregator".
  - Update the "Getting Started" or database configuration section to explicitly mandate connecting to Supabase for both local development and Azure production deployments. Remove instructions suggesting the Docker database is the primary local DB.

## 3. Validation
- Run the scraper locally to verify it correctly skips PG courses and only upserts UG courses.
- Verify the local application and scraper can successfully connect to the provided Supabase database URL.

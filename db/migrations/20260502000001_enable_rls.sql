-- migrate:up

-- Public read tables (course discovery data — intentionally world-readable)
ALTER TABLE universities       ENABLE ROW LEVEL SECURITY;
ALTER TABLE campuses           ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses            ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_campuses    ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_prerequisites ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculties          ENABLE ROW LEVEL SECURITY;
ALTER TABLE campus_aliases     ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read" ON universities       FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read" ON campuses           FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read" ON courses            FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read" ON course_campuses    FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read" ON course_prerequisites FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read" ON faculties          FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read" ON campus_aliases     FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Service role full access" ON universities       FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON campuses           FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON courses            FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON course_campuses    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON course_prerequisites FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON faculties          FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON campus_aliases     FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Internal / scraper tables (service role only)
ALTER TABLE scraper_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_queue    ENABLE ROW LEVEL SECURITY;
ALTER TABLE atar_issues     ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON scraper_configs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON scrape_runs     FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON scrape_queue    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON atar_issues     FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Leads: anonymous INSERT (form submissions), service role full access
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anon can submit leads" ON leads FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Service role full access" ON leads FOR ALL TO service_role USING (true) WITH CHECK (true);

-- migrate:down
-- Public tables
DROP POLICY "Public read"              ON universities;
DROP POLICY "Service role full access" ON universities;
DROP POLICY "Public read"              ON campuses;
DROP POLICY "Service role full access" ON campuses;
DROP POLICY "Public read"              ON courses;
DROP POLICY "Service role full access" ON courses;
DROP POLICY "Public read"              ON course_campuses;
DROP POLICY "Service role full access" ON course_campuses;
DROP POLICY "Public read"              ON course_prerequisites;
DROP POLICY "Service role full access" ON course_prerequisites;
DROP POLICY "Public read"              ON faculties;
DROP POLICY "Service role full access" ON faculties;
DROP POLICY "Public read"              ON campus_aliases;
DROP POLICY "Service role full access" ON campus_aliases;
ALTER TABLE universities        DISABLE ROW LEVEL SECURITY;
ALTER TABLE campuses            DISABLE ROW LEVEL SECURITY;
ALTER TABLE courses             DISABLE ROW LEVEL SECURITY;
ALTER TABLE course_campuses     DISABLE ROW LEVEL SECURITY;
ALTER TABLE course_prerequisites DISABLE ROW LEVEL SECURITY;
ALTER TABLE faculties           DISABLE ROW LEVEL SECURITY;
ALTER TABLE campus_aliases      DISABLE ROW LEVEL SECURITY;

-- Internal tables
DROP POLICY "Service role full access" ON scraper_configs;
DROP POLICY "Service role full access" ON scrape_runs;
DROP POLICY "Service role full access" ON scrape_queue;
DROP POLICY "Service role full access" ON atar_issues;
ALTER TABLE scraper_configs DISABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs     DISABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_queue    DISABLE ROW LEVEL SECURITY;
ALTER TABLE atar_issues     DISABLE ROW LEVEL SECURITY;

-- Leads
DROP POLICY "Anon can submit leads"    ON leads;
DROP POLICY "Service role full access" ON leads;
ALTER TABLE leads DISABLE ROW LEVEL SECURITY;

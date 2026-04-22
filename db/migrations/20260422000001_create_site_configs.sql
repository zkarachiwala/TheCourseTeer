-- migrate:up
CREATE TABLE site_configs (
    id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id      uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    base_url           text        NOT NULL,
    extraction_map     jsonb       NOT NULL,
    robots_txt_status  text,
    version            integer     NOT NULL DEFAULT 1,
    is_active          boolean     NOT NULL DEFAULT true,
    sample_urls        text[]      DEFAULT '{}',
    notes              text,
    last_updated       timestamptz DEFAULT now(),
    created_at         timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE site_configs ENABLE ROW LEVEL SECURITY;

-- Define Security Policies
-- Allow service_role full access
CREATE POLICY "Service role has full access" ON site_configs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow authenticated users read-only access
CREATE POLICY "Authenticated users can view active configs" ON site_configs
    FOR SELECT
    TO authenticated
    USING (is_active = true);

-- migrate:down
DROP TABLE site_configs;

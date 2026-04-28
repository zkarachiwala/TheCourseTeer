-- Create campus_aliases table to support multiple acronyms/codes per campus
CREATE TABLE campus_aliases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    campus_id uuid NOT NULL REFERENCES campuses(id) ON DELETE CASCADE,
    alias_code text NOT NULL,
    created_at timestamptz DEFAULT now(),
    UNIQUE(campus_id, alias_code)
);

-- Index for fast lookups
CREATE INDEX idx_campus_aliases_code ON campus_aliases (alias_code);

-- Migrate existing external_codes to the new table
INSERT INTO campus_aliases (campus_id, alias_code)
SELECT id, external_code FROM campuses WHERE external_code IS NOT NULL;

-- We can now drop external_code from campuses or keep it as the 'primary' code
-- Recommendation: Remove it to avoid duplicate sources of truth
ALTER TABLE campuses DROP COLUMN external_code;

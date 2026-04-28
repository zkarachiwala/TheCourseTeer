-- Add external_code to campuses to support university-specific acronyms (e.g. 'BU' for Bundoora)
ALTER TABLE campuses ADD COLUMN external_code text;

-- Add index for lookups
CREATE INDEX idx_campuses_university_external_code ON campuses (university_id, external_code);

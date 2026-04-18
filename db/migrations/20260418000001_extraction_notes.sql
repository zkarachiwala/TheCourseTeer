-- migrate:up
ALTER TABLE course_campuses ADD COLUMN extraction_notes text;

-- migrate:down
ALTER TABLE course_campuses DROP COLUMN extraction_notes;

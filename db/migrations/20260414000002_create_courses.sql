-- migrate:up
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE courses (
    id                          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id               uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name                        text        NOT NULL,
    faculty                     text,
    campus                      text,
    degree_type                 text        NOT NULL,
    duration_years              numeric,
    source_url                  text,
    price_annual_csp_aud        integer,
    price_annual_dfee_aud       integer,
    csp_available               boolean,
    atar_guaranteed             integer,
    atar_lowest_selection_rank  integer,
    prerequisites               jsonb,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX courses_university_id_idx
    ON courses(university_id);

CREATE INDEX courses_degree_type_idx
    ON courses(degree_type);

CREATE INDEX courses_university_id_degree_type_idx
    ON courses(university_id, degree_type);

CREATE OR REPLACE TRIGGER courses_set_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- migrate:down
DROP TRIGGER courses_set_updated_at ON courses;
DROP TABLE courses;
DROP FUNCTION set_updated_at;

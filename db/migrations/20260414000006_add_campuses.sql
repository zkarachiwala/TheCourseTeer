-- migrate:up
CREATE TABLE campuses (
    id            uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid    NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name          text    NOT NULL,
    slug          text    NOT NULL,
    address       text,
    UNIQUE (university_id, slug),
    latitude      numeric,
    longitude     numeric
);

CREATE INDEX campuses_university_id_idx
    ON campuses(university_id);

ALTER TABLE courses
    DROP COLUMN campus;

ALTER TABLE courses
    ADD COLUMN campus_id uuid REFERENCES campuses(id) ON DELETE SET NULL;

CREATE INDEX courses_campus_id_idx
    ON courses(campus_id);

-- migrate:down
DROP INDEX courses_campus_id_idx;

ALTER TABLE courses
    DROP COLUMN campus_id;

ALTER TABLE courses
    ADD COLUMN campus text;

DROP TABLE campuses;

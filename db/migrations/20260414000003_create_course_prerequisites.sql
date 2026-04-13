-- migrate:up
CREATE TABLE course_prerequisites (
    course_id          uuid NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    requires_course_id uuid NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    notes              text,
    PRIMARY KEY (course_id, requires_course_id)
);

-- PK index covers (course_id, ...) lookups; this covers the reverse direction.
CREATE INDEX course_prerequisites_requires_course_id_idx
    ON course_prerequisites(requires_course_id);

-- migrate:down
DROP TABLE course_prerequisites;

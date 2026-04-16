-- migrate:up
CREATE TABLE course_campuses (
    course_id  uuid NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    campus_id  uuid NOT NULL REFERENCES campuses(id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, campus_id)
);

CREATE INDEX course_campuses_campus_id_idx
    ON course_campuses(campus_id);

-- Migrate existing RMIT course->campus assignments before dropping the column
INSERT INTO course_campuses (course_id, campus_id)
SELECT c.id, c.campus_id
FROM courses c
JOIN universities u ON c.university_id = u.id
WHERE u.slug = 'rmit'
  AND c.campus_id IS NOT NULL;

ALTER TABLE courses
    DROP COLUMN campus_id;

-- migrate:down
ALTER TABLE courses
    ADD COLUMN campus_id uuid REFERENCES campuses(id) ON DELETE SET NULL;

CREATE INDEX courses_campus_id_idx
    ON courses(campus_id);

-- Best-effort restore: write back the first campus for each course
UPDATE courses c
SET campus_id = cc.campus_id
FROM (
    SELECT DISTINCT ON (course_id) course_id, campus_id
    FROM course_campuses
    ORDER BY course_id
) cc
WHERE c.id = cc.course_id;

DROP TABLE course_campuses;

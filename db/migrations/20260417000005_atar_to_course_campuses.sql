-- migrate:up

ALTER TABLE course_campuses
    ADD COLUMN atar_guaranteed            integer,
    ADD COLUMN atar_lowest_selection_rank integer;

-- Migrate RMIT ATAR data (one campus per course)
UPDATE course_campuses cc
SET atar_guaranteed            = c.atar_guaranteed,
    atar_lowest_selection_rank = c.atar_lowest_selection_rank
FROM courses c
JOIN universities u ON c.university_id = u.id
WHERE cc.course_id = c.id
  AND u.slug = 'rmit';

ALTER TABLE courses
    DROP COLUMN atar_guaranteed,
    DROP COLUMN atar_lowest_selection_rank;

-- migrate:down

ALTER TABLE courses
    ADD COLUMN atar_guaranteed            integer,
    ADD COLUMN atar_lowest_selection_rank integer;

-- Best-effort restore: write back RMIT ATAR from join table
UPDATE courses c
SET atar_guaranteed            = cc.atar_guaranteed,
    atar_lowest_selection_rank = cc.atar_lowest_selection_rank
FROM course_campuses cc
JOIN universities u ON c.university_id = u.id
WHERE cc.course_id = c.id
  AND u.slug = 'rmit';

ALTER TABLE course_campuses
    DROP COLUMN atar_guaranteed,
    DROP COLUMN atar_lowest_selection_rank;

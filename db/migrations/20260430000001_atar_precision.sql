-- migrate:up
ALTER TABLE course_campuses
    ALTER COLUMN atar_guaranteed TYPE numeric(5,2),
    ALTER COLUMN atar_lowest_selection_rank TYPE numeric(5,2);

-- migrate:down
ALTER TABLE course_campuses
    ALTER COLUMN atar_guaranteed TYPE integer,
    ALTER COLUMN atar_lowest_selection_rank TYPE integer;

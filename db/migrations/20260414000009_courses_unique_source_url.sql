-- migrate:up
ALTER TABLE courses
    ADD CONSTRAINT courses_university_id_source_url_key
    UNIQUE (university_id, source_url);

-- migrate:down
ALTER TABLE courses
    DROP CONSTRAINT courses_university_id_source_url_key;

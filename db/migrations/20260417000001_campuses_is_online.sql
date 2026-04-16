-- migrate:up
ALTER TABLE campuses
    ADD COLUMN is_online boolean NOT NULL DEFAULT false;

-- migrate:down
ALTER TABLE campuses
    DROP COLUMN is_online;

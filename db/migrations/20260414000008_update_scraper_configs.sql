-- migrate:up
ALTER TABLE scraper_configs
    ADD COLUMN mode text NOT NULL DEFAULT 'static' CHECK (mode IN ('static', 'browser'));

ALTER TABLE scraper_configs
    ADD CONSTRAINT scraper_configs_university_id_field_name_key
    UNIQUE (university_id, field_name);

DROP INDEX scraper_configs_university_id_field_name_idx;

-- migrate:down
ALTER TABLE scraper_configs
    DROP CONSTRAINT scraper_configs_university_id_field_name_key;

ALTER TABLE scraper_configs
    DROP COLUMN mode;

CREATE INDEX scraper_configs_university_id_field_name_idx
    ON scraper_configs(university_id, field_name);

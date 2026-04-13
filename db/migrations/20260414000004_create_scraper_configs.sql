-- migrate:up
CREATE TABLE scraper_configs (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id    uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    field_name       text        NOT NULL,
    selector         text        NOT NULL,
    last_verified_at timestamptz,
    ai_generated     boolean     NOT NULL DEFAULT false
);

CREATE INDEX scraper_configs_university_id_field_name_idx
    ON scraper_configs(university_id, field_name);

-- migrate:down
DROP TABLE scraper_configs;

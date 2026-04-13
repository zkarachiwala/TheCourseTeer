-- migrate:up
CREATE TABLE universities (
    id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name           text        NOT NULL,
    slug           text        NOT NULL UNIQUE,
    homepage_url   text        NOT NULL,
    scraper_status text        NOT NULL DEFAULT 'pending',
    robots_txt_rules jsonb,
    last_scraped_at timestamptz
);

-- migrate:down
DROP TABLE universities;

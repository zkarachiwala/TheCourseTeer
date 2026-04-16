-- migrate:up
CREATE TABLE scrape_runs (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id       uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    run_number          int         NOT NULL,
    discovery_complete  boolean     NOT NULL DEFAULT false,
    status              text        NOT NULL DEFAULT 'in_progress',
    forced              boolean     NOT NULL DEFAULT false,
    started_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz,
    UNIQUE (university_id, run_number)
);

CREATE INDEX scrape_runs_university_status_idx
    ON scrape_runs(university_id, status);

CREATE TABLE scrape_queue (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id       uuid        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    discovered_run_id   uuid        NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
    completed_run_id    uuid        REFERENCES scrape_runs(id) ON DELETE SET NULL,
    url                 text        NOT NULL,
    status              text        NOT NULL DEFAULT 'pending',
    attempt_count       int         NOT NULL DEFAULT 0,
    last_error          text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (university_id, url)
);

CREATE INDEX scrape_queue_university_status_idx
    ON scrape_queue(university_id, status);

CREATE OR REPLACE TRIGGER scrape_queue_set_updated_at
    BEFORE UPDATE ON scrape_queue
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- migrate:down
DROP TRIGGER scrape_queue_set_updated_at ON scrape_queue;
DROP TABLE scrape_queue;
DROP TABLE scrape_runs;

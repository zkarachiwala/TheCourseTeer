-- migrate:up

CREATE TABLE atar_issues (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id   uuid NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    run_id          uuid NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
    course_name     text NOT NULL,
    course_url      text NOT NULL,
    issue_type      text NOT NULL,
    description     text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX atar_issues_university_id ON atar_issues(university_id);
CREATE INDEX atar_issues_run_id ON atar_issues(run_id);

-- migrate:down

DROP TABLE atar_issues;

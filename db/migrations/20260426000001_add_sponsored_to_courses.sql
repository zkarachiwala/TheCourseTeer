-- migrate:up
ALTER TABLE courses
  ADD COLUMN IF NOT EXISTS sponsored BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS sponsored_rank INTEGER;

-- migrate:down
ALTER TABLE courses
  DROP COLUMN IF EXISTS sponsored,
  DROP COLUMN IF EXISTS sponsored_rank;

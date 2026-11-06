-- Quality: row and table checks, rejects, volume and schema drift, source health.
-- Idempotent; every load lands a row in quality_runs.

CREATE TABLE quality_runs (
  run_id      bigserial PRIMARY KEY,
  source      text      NOT NULL,
  run_at      timestamptz NOT NULL DEFAULT now(),
  ok          boolean   NOT NULL,
  message     text,
  null_rates  jsonb,
  duplicates  integer   NOT NULL DEFAULT 0,
  outliers    integer   NOT NULL DEFAULT 0,
  sector_spread jsonb,
  volume_drift boolean,
  schema_drift jsonb
);

CREATE INDEX quality_runs_source_idx ON quality_runs (source, run_at DESC);

CREATE TABLE rejects (
  reject_id   bigserial PRIMARY KEY,
  source      text      NOT NULL,
  source_id   text,
  raw_id      bigint REFERENCES raw_manifest(id),
  reason      text      NOT NULL,
  row_json    jsonb     NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX rejects_source_idx ON rejects (source);

-- One row per source: the latest quality run, whether it was ok, and how many
-- raw payloads each source has fetched. Read by the read-only role.
CREATE OR REPLACE VIEW source_health AS
SELECT
  m.source,
  (SELECT MAX(q2.run_id) FROM quality_runs q2 WHERE q2.source = m.source) AS last_quality_run,
  (SELECT MAX(q2.run_at) FROM quality_runs q2 WHERE q2.source = m.source) AS last_run_at,
  (SELECT q2.ok FROM quality_runs q2 WHERE q2.source = m.source
   ORDER BY q2.run_at DESC NULLS LAST LIMIT 1) AS last_run_ok,
  COUNT(*) AS raw_fetches
FROM raw_manifest m
GROUP BY m.source;

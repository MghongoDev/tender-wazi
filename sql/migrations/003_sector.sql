-- Sector labels, one row per notice, beside the versions.
-- A notice can carry several sectors. The rules version records which rules
-- produced the labels, so a change to the rules means a full re-run.

CREATE TABLE tender_sector (
  source        text NOT NULL,
  source_id     text NOT NULL,
  sectors       text[] NOT NULL,
  matched_terms text[] NOT NULL DEFAULT '{}',
  rules_version text NOT NULL,
  classified_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (source, source_id)
);

CREATE INDEX tender_sector_gin ON tender_sector USING gin (sectors);

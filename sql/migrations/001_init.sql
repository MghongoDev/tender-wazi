CREATE TABLE raw_manifest (
  id          bigserial PRIMARY KEY,
  source      text NOT NULL,
  url         text NOT NULL,
  fetched_at  timestamptz NOT NULL,
  http_status int NOT NULL,
  sha256      text NOT NULL,
  object_key  text NOT NULL
);
CREATE INDEX raw_manifest_source_idx ON raw_manifest (source, fetched_at DESC);

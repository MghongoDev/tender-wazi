-- Portal B detail records, so the schema-drift check can measure field
-- coverage without re-parsing. Idempotent: a notice wins on source_id.
CREATE TABLE portal_b_details (
  source_id         text PRIMARY KEY,
  title             text,
  published_at_raw  text,
  closing_at_raw    text,
  category_raw      text,
  notice_type       text,
  document_links    text[],
  raw_id            bigint REFERENCES raw_manifest(id)
);

CREATE INDEX portal_b_details_source_id_idx
  ON portal_b_details (source_id);

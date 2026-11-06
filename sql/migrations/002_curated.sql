-- Curated model: staging tables, versioned notices, lineage.
-- The raw layer stays in object storage; only normalized fields live here.

CREATE TABLE staging_ppip_tenders (
  ocid               text PRIMARY KEY,
  buyer_name         text,
  title              text,
  category_raw       text,
  procurement_method text,
  published_at       text,
  closing_at         text,
  status             text,
  value_amount       numeric,
  currency           text,
  raw_id             bigint REFERENCES raw_manifest(id)
);

CREATE TABLE staging_portal_b_tenders (
  source_id        text PRIMARY KEY,
  title            text,
  category_raw     text,
  notice_type      text,
  published_at_raw text,
  closing_at_raw   text,
  document_links   text[],
  raw_id           bigint REFERENCES raw_manifest(id)
);

CREATE TABLE tender_versions (
  id                 bigserial PRIMARY KEY,
  source             text        NOT NULL,
  source_id          text        NOT NULL,
  version_no         int         NOT NULL,
  content_hash       text        NOT NULL,
  valid_from         timestamptz NOT NULL DEFAULT now(),
  valid_to           timestamptz,
  title              text,
  buyer_name         text,
  category           text,
  category_raw       text,
  notice_type        text,
  procurement_method text,
  status             text,
  jurisdiction       text,
  published_at       timestamptz,
  closing_at         timestamptz,
  value_amount       numeric,
  currency           text,
  source_url         text,
  raw_id             bigint REFERENCES raw_manifest(id),
  search             tsvector GENERATED ALWAYS AS (
                       to_tsvector('simple',
                         coalesce(title,'') || ' ' || coalesce(buyer_name,'') || ' ' || coalesce(category_raw,''))
                     ) STORED,
  UNIQUE (source, source_id, version_no)
);

-- At most one open version per notice.
CREATE UNIQUE INDEX one_open_version ON tender_versions (source, source_id) WHERE valid_to IS NULL;
CREATE INDEX tender_search_idx ON tender_versions USING gin (search) WHERE valid_to IS NULL;
CREATE INDEX tender_published_idx ON tender_versions (published_at DESC, id DESC) WHERE valid_to IS NULL;

CREATE TABLE tender_seen (
  source        text NOT NULL,
  source_id     text NOT NULL,
  first_seen_at timestamptz NOT NULL,
  last_seen_at  timestamptz NOT NULL,
  PRIMARY KEY (source, source_id)
);

-- Every version of a notice, with the raw payload it came from.
CREATE VIEW tender_lineage AS
SELECT v.*, r.url AS raw_url, r.fetched_at AS raw_fetched_at,
       r.sha256 AS raw_sha256, r.object_key
FROM tender_versions v
LEFT JOIN raw_manifest r ON r.id = v.raw_id;

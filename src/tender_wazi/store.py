from tender_wazi.normalize import content_hash

COLUMNS = (
    "source",
    "source_id",
    "title",
    "buyer_name",
    "category",
    "category_raw",
    "notice_type",
    "procurement_method",
    "status",
    "jurisdiction",
    "published_at",
    "closing_at",
    "value_amount",
    "currency",
    "source_url",
    "raw_id",
)

INCOMING_COLUMNS = COLUMNS + ("content_hash",)

INCOMING_SQL = """
CREATE TEMP TABLE incoming (
  source             text,
  source_id          text,
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
  raw_id             bigint,
  content_hash       text
) ON COMMIT DROP
"""

UPSERT_SQL = """
-- 1. close open versions whose content changed
UPDATE tender_versions v
SET valid_to = now()
FROM incoming i
WHERE v.source = i.source AND v.source_id = i.source_id
  AND v.valid_to IS NULL AND v.content_hash <> i.content_hash;

-- 2. insert version 1 for new notices and the next version for changed ones
INSERT INTO tender_versions (source, source_id, version_no, content_hash, title, buyer_name,
                             category, category_raw, notice_type, procurement_method, status,
                             jurisdiction, published_at, closing_at, value_amount, currency,
                             source_url, raw_id)
SELECT i.source, i.source_id,
       COALESCE((SELECT max(version_no) FROM tender_versions m
                 WHERE m.source = i.source AND m.source_id = i.source_id), 0) + 1,
       i.content_hash, i.title, i.buyer_name, i.category, i.category_raw, i.notice_type,
       i.procurement_method, i.status, i.jurisdiction, i.published_at, i.closing_at,
       i.value_amount, i.currency, i.source_url, i.raw_id
FROM incoming i
WHERE NOT EXISTS (SELECT 1 FROM tender_versions o
                  WHERE o.source = i.source AND o.source_id = i.source_id AND o.valid_to IS NULL);

-- 3. record that we saw it today
INSERT INTO tender_seen (source, source_id, first_seen_at, last_seen_at)
SELECT source, source_id, now(), now() FROM incoming
ON CONFLICT (source, source_id) DO UPDATE SET last_seen_at = EXCLUDED.last_seen_at;
"""

PPIP_STAGING_FIELDS = (
    "ocid",
    "buyer_name",
    "title",
    "category_raw",
    "procurement_method",
    "published_at",
    "closing_at",
    "status",
    "value_amount",
    "currency",
    "raw_id",
)

PORTAL_B_STAGING_FIELDS = (
    "source_id",
    "title",
    "category_raw",
    "notice_type",
    "published_at_raw",
    "closing_at_raw",
    "document_links",
    "raw_id",
)


def store_batch(conn, rows):
    """Load a batch of normalized rows, versioning changed notices.

    A notice whose content changed gets a new version and its old version is
    closed in the same transaction, so valid_to and valid_from match with no
    gap and no overlap. An unchanged notice adds no version.
    """
    deduped = {}
    for row in rows:
        deduped[(row["source"], row["source_id"])] = row

    with conn.cursor() as cur:
        cur.execute(INCOMING_SQL)
        with cur.copy(f"COPY incoming ({', '.join(INCOMING_COLUMNS)}) FROM STDIN") as copy:
            for row in deduped.values():
                values = {key: row.get(key) for key in COLUMNS}
                values["content_hash"] = content_hash(row)
                copy.write_row(tuple(values[key] for key in INCOMING_COLUMNS))
        cur.execute(UPSERT_SQL)
    conn.commit()


def load_ppip_staging(conn, rows):
    """Land the parsed PPIP rows in the staging table, idempotently."""
    columns = ", ".join(PPIP_STAGING_FIELDS)
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TEMP TABLE staging_temp (ocid text, buyer_name text, title text, "
            "category_raw text, procurement_method text, published_at text, closing_at text, "
            "status text, value_amount numeric, currency text, raw_id bigint) ON COMMIT DROP"
        )
        with cur.copy(f"COPY staging_temp ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(tuple(row.get(key) for key in PPIP_STAGING_FIELDS))
        cur.execute(
            "INSERT INTO staging_ppip_tenders (ocid, buyer_name, title, category_raw, "
            "procurement_method, published_at, closing_at, status, value_amount, currency, raw_id) "
            "SELECT ocid, buyer_name, title, category_raw, procurement_method, published_at, "
            "closing_at, status, value_amount, currency, raw_id FROM staging_temp "
            "ON CONFLICT (ocid) DO UPDATE SET buyer_name = EXCLUDED.buyer_name, "
            "title = EXCLUDED.title, category_raw = EXCLUDED.category_raw, "
            "procurement_method = EXCLUDED.procurement_method, "
            "published_at = EXCLUDED.published_at, closing_at = EXCLUDED.closing_at, "
            "status = EXCLUDED.status, value_amount = EXCLUDED.value_amount, "
            "currency = EXCLUDED.currency, raw_id = EXCLUDED.raw_id"
        )
    conn.commit()


def load_portal_b_staging(conn, rows):
    """Land the parsed Kenya Power rows in the staging table, idempotently."""
    columns = ", ".join(PORTAL_B_STAGING_FIELDS)
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TEMP TABLE staging_temp (source_id text, title text, category_raw text, "
            "notice_type text, published_at_raw text, closing_at_raw text, "
            "document_links text[], raw_id bigint) ON COMMIT DROP"
        )
        with cur.copy(f"COPY staging_temp ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(tuple(row.get(key) for key in PORTAL_B_STAGING_FIELDS))
        cur.execute(
            "INSERT INTO staging_portal_b_tenders (source_id, title, category_raw, notice_type, "
            "published_at_raw, closing_at_raw, document_links, raw_id) "
            "SELECT source_id, title, category_raw, notice_type, published_at_raw, "
            "closing_at_raw, document_links, raw_id FROM staging_temp "
            "ON CONFLICT (source_id) DO UPDATE SET title = EXCLUDED.title, "
            "category_raw = EXCLUDED.category_raw, notice_type = EXCLUDED.notice_type, "
            "published_at_raw = EXCLUDED.published_at_raw, "
            "closing_at_raw = EXCLUDED.closing_at_raw, "
            "document_links = EXCLUDED.document_links, raw_id = EXCLUDED.raw_id"
        )
    conn.commit()

# Data dictionary

The curated model. The raw payloads live in object storage. Only normalized fields live in Postgres.

## tender_versions

One row per version of a notice. At most one row per (source, source_id) has a null valid_to.

| Field | Type | Notes |
|---|---|---|
| id | bigint | Primary key. |
| source | text | ppip or portal_b. |
| source_id | text | The PPIP ocid, or the Kenya Power reference number. |
| version_no | int | Starts at 1 and increases by one per change. |
| content_hash | text | sha256 over the business fields, listed below. |
| valid_from | timestamptz | When this version opened. |
| valid_to | timestamptz | When this version closed. Null while it is current. |
| title | text | |
| buyer_name | text | |
| category | text | goods, works, services, consultancy or other. |
| category_raw | text | As the source states it. |
| notice_type | text | As the source states it. Null when the source does not state one. |
| procurement_method | text | |
| status | text | |
| jurisdiction | text | national or county. |
| published_at | timestamptz | |
| closing_at | timestamptz | |
| value_amount | numeric | |
| currency | text | |
| source_url | text | |
| raw_id | bigint | Points at raw_manifest.id. |
| search | tsvector | Title, buyer and category_raw, for full-text search. |

The content hash covers title, buyer_name, category, category_raw, notice_type, procurement_method, status, jurisdiction, published_at, closing_at, value_amount, currency and source_url. It never covers fetch times, raw_id or the sector label, so re-fetching an unchanged notice gives the same hash.

## tender_seen

One row per notice ever seen.

| Field | Type | Notes |
|---|---|---|
| source | text | |
| source_id | text | |
| first_seen_at | timestamptz | |
|| last_seen_at | timestamptz | A notice missing from a later complete fetch keeps an older last_seen_at. |

## tender_sector

One row per notice with its sector labels. The classifier never changes
tender_versions.

| Field | Type | Notes |
|---|---|---|
| source | text | ppip or portal_b. |
| source_id | text | The PPIP ocid, or the Kenya Power reference number. |
| sectors | text[] | One or more sectors. |
| matched_terms | text[] | The terms that matched. |
| rules_version | text | The rules version that produced these labels. |
| classified_at | timestamptz | When the labels were written. |

## tender_lineage

A view that joins every version to its raw_manifest row: the version fields plus raw_url, raw_fetched_at, raw_sha256 and object_key.

## staging_ppip_tenders

One row per PPIP contracting process, keyed by ocid. The parsed dates stay as text here and become timestamptz in tender_versions.

## staging_portal_b_tenders

One row per Kenya Power notice, keyed by the reference number. The raw dates and document links stay as the page states them.

## Category set

goods, works, services, consultancy, other. Map only what the source states. Send everything unclear to other.

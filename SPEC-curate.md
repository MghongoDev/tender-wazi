# Spec: curate

## Objective

Normalize the two sources into one schema, version changed notices, and keep the history. The raw layer stays the source of truth for re-normalization.

Success looks like: both sources load into `tender_versions`; a changed notice creates exactly one new version and closes the old one; an unchanged notice creates no new version; `tender_lineage` returns every version with its `raw_manifest` row.

## Tech Stack

- Python 3.12, uv
- psycopg 3 for the load and the versioned upsert
- Numbered SQL migrations through the shared runner (`src/tender_wazi/migrate.py`)
- pytest for tests

## Commands

Migrate:

```
uv run python -m tender_wazi migrate
```

Run (collect, normalize, store):

```
uv run python -m tender_wazi run --source ppip --year 2025
uv run python -m tender_wazi run --source portal_b
```

Test:

```
uv run pytest -q
```

Verify:

```
psql "$DATABASE_URL_DIRECT" -c "select source, count(*) from tender_versions where valid_to is null group by 1"
psql "$DATABASE_URL_DIRECT" -c "select source, source_id, count(*) from tender_versions group by 1,2 order by 3 desc limit 5"
```

## Project Structure

```
src/tender_wazi/
  normalize.py      parsed rows -> one normalized schema
  store.py          versioned upsert, tender_seen
  sources/
    ppip.py         collect: parse_line
    portal_b.py     collect: parse_detail
sql/migrations/
  002_curated.sql  staging tables, tender_versions, tender_seen, tender_lineage
tests/
  test_normalize.py
  test_store.py
```

## Documentation

- docs/reference/data-dictionary.md — the curated schema.
- docs/explanation/decisions.md — the decisions.
- GLOSSARY.md — the domain vocabulary.
- README.md — the entry point.

## Code Style

Normalization is a pure function from a parsed row to the normalized dict, so tests can feed it fixtures:

```python
def normalize_ppip(row: dict) -> dict:
    return {
        "source": "ppip",
        "source_id": row["ocid"],
        "title": row["title"],
        "buyer_name": row["buyer_name"],
        "category": normalize_category(row["category_raw"]),
        "category_raw": row["category_raw"],
        "notice_type": None,
        "procurement_method": row["procurement_method"],
        "status": row["status"],
        "jurisdiction": jurisdiction(row["buyer_name"]),
        "published_at": parse_datetime(row["published_at"]),
        "closing_at": parse_datetime(row["closing_at"]),
        "value_amount": row["value_amount"],
        "currency": row["currency"],
        "source_url": f"https://tenders.go.ke/ocds/{row['ocid']}",
    }
```

The versioned upsert is SQL, in one transaction, so a closed version's `valid_to` equals the new version's `valid_from`:

```sql
UPDATE tender_versions v
SET valid_to = now()
FROM incoming i
WHERE v.source = i.source AND v.source_id = i.source_id
  AND v.valid_to IS NULL AND v.content_hash <> i.content_hash;
```

The content hash covers the business fields only: title, buyer, category, notice type, method, status, jurisdiction, dates, value, currency and source URL. It never covers fetch times, `raw_id` or the sector label.

## Testing Strategy

- Unit tests for normalize: each source's mapping, the category normalization, the date parsing and the content hash.
- Integration tests for store: load a batch, change one field, load again, and assert exactly one new version with the old one closed; load the same batch twice and assert no new versions.
- Fixtures: the saved raw payloads, plus a small hand-built batch for the version tests.

## Boundaries

- Always: compute the content hash over the business fields only; run the versioned upsert in one transaction; keep the raw layer as the source for re-normalization.
- Ask first: changing the normalized schema; changing the category set; adding a source.
- Never: store the full OCDS payload in Postgres; put the sector label in `tender_versions`; delete or edit a version in place.

## Success Criteria

- `uv run pytest -q` passes.
- `uv run python -m tender_wazi migrate` applies `002_curated.sql`.
- Both sources load into `tender_versions`, and the open-version counts match the raw parses.
- A changed notice creates exactly one new version with the old one closed; an unchanged notice creates none.
- `tender_lineage` returns every version with its `raw_manifest` row.
- A second identical run adds no versions.

## Assumptions

1. The normalized schema is the guide's `tender_versions` table.
2. `source_id` is the PPIP `ocid` and the Kenya Power reference number.
3. The content hash covers the business fields only, not fetch times or the sector label.
4. Dates: PPIP carries an offset; Kenya Power has none, so assume Africa/Nairobi (+03:00).
5. Jurisdiction: national unless the buyer name names a county.
6. Staging tables hold the parsed rows before normalization, so a load is idempotent.
7. The sector label is added later by classify, outside `tender_versions`.

## Open Questions

1. The PPIP category set on the full dataset. Answered by the first load: goods, services, works and other. The mapping needs no extension.
2. Kenya Power states no category and no notice type. The normalized category is other and the raw fields stay null. Deriving them from the title belongs to the classify module.
3. The jurisdiction heuristic (buyer name contains "County") is crude. Accepted for the MVP.

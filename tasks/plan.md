# Plan: curate

## Goal

Normalize both sources into one schema, version changed notices, and keep the history. Update the documentation at each step.

## Steps

1. Write `sql/migrations/002_curated.sql`: `staging_ppip_tenders`, `staging_portal_b_tenders`, `tender_versions`, `tender_seen`, `tender_lineage`. Apply it.
2. Write `tests/test_normalize.py`, then `src/tender_wazi/normalize.py`: `parse_datetime`, `jurisdiction`, `normalize_ppip`, `normalize_portal_b`, `content_hash`.
3. Write `tests/test_store.py`, then `src/tender_wazi/store.py`: the three-step versioned upsert.
4. Extend the CLI so `run --source ppip --year 2025` and `run --source portal_b` also normalize and store.
5. Run the first load for both sources into dev. Verify the counts and the version behaviour.
6. Update the docs: data dictionary, decisions, README, glossary.

## Risks

- The PPIP category set on the full dataset is unknown; the mapping may need extending after the first load.
- The date parsing must handle both the PPIP ISO strings and the Kenya Power DD/MM/YYYY strings.
- The versioned upsert must be idempotent, so a rerun adds no versions.

## Verification

- `uv run pytest -q`.
- `psql "$DATABASE_URL_DIRECT" -c "select source, count(*) from tender_versions where valid_to is null group by 1"`.
- A changed notice creates exactly one new version; an unchanged one creates none.

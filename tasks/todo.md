# Tasks: curate

- [x] Write `sql/migrations/002_curated.sql` and apply it
  - Verified: the staging tables, `tender_versions`, `tender_seen` and `tender_lineage` exist on dev
- [x] Write `tests/test_normalize.py` and `src/tender_wazi/normalize.py`
  - Verified: 8 unit tests pass
- [x] Write `tests/test_store.py` and `src/tender_wazi/store.py`
  - Verified: 3 integration tests pass
- [x] Extend the CLI to normalize and store
  - Verified: `run --source ppip --year 2025` fills the staging and curated tables
- [x] Run the first load for both sources
  - Verified: ppip 33,258 and portal_b 9 open versions
- [x] Update the docs
  - Verified: the data dictionary, decisions, how-to, glossary and README reflect the curated model

# Tasks: curate

- [ ] Write `sql/migrations/002_curated.sql` and apply it
  - Verify: the staging tables, `tender_versions`, `tender_seen` and `tender_lineage` exist on dev
- [ ] Write `tests/test_normalize.py` and `src/tender_wazi/normalize.py`
  - Verify: the unit tests pass
- [ ] Write `tests/test_store.py` and `src/tender_wazi/store.py`
  - Verify: the integration tests
- [ ] Extend the CLI to normalize and store
  - Verify: `run --source ppip --year 2025` fills both the raw and the curated tables
- [ ] Run the first load for both sources
  - Verify: the open-version counts match the raw parses
- [ ] Update the docs
  - Verify: the data dictionary, decisions, README and glossary reflect the curated model

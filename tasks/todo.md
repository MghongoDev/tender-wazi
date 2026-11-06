# Tasks: classify

- [ ] Write `config/sector_rules.yaml`
  - Verify: the version is a non-empty string and every sector has an `any` list
- [ ] Write `tests/test_sectors.py` and `src/tender_wazi/sectors.py`
  - Verify: the unit tests pass
- [ ] Write `sql/migrations/003_sector.sql` and apply it
  - Verify: `tender_sector` exists on dev
- [ ] Add the `classify` CLI command
  - Verify: `uv run python -m tender_wazi classify` labels every current notice
- [ ] Run the classifier and check the sector spread
  - Verify: the counts per sector look sensible
- [ ] Pull and label the sample, write `tests/sector_labels.csv`, compute the precision and miss rate
  - Verify: the tech label's precision is at or above 85%
- [ ] Update the docs
  - Verify: sector-method.md, the data dictionary, decisions, glossary and README reflect the classifier

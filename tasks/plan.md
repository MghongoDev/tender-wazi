# Plan: classify

## Goal

Label every current notice with sectors from a fixed taxonomy, store the matched terms and the rules version, and measure the tech label's precision and miss rate. Update the documentation at each step.

## Steps

1. Write `config/sector_rules.yaml`: a version string and terms per sector. Start with the guide's tech list.
2. Write `tests/test_sectors.py`, then `src/tender_wazi/sectors.py`: `load_rules`, `classify`.
3. Write `sql/migrations/003_sector.sql`: `tender_sector`. Apply it.
4. Add the `classify` CLI command: label every current notice and upsert.
5. Run `classify` on dev. Verify the sector spread.
6. Pull the hand-labelled sample (100 tagged `ict_data_tech`, 100 not), label it, write `tests/sector_labels.csv`, and compute the precision and miss rate.
7. Improve the rules from the errors, bump the version, and measure again.
8. Update the docs: sector-method.md, data dictionary, decisions, glossary, README.

## Risks

- The rules will have false positives. The labelled sample finds them.
- The sample must be drawn at random across both sources.
- The rules version must change when the terms change, or the labels go stale.

## Verification

- `uv run pytest -q`.
- `psql "$DATABASE_URL_DIRECT" -c "select unnest(sectors), count(*) from tender_sector group by 1 order by 2 desc"`.
- The tech label's precision is at or above 85% on the labelled sample.

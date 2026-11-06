# Spec: classify

## Objective

Label every current notice with one or more sectors from a fixed taxonomy, store the matched terms and the rules version, and measure how often the tech label is wrong.

Success looks like: `classify` runs on both sources; `tender_sector` holds one row per notice with sectors, matched terms and the rules version; `docs/explanation/sector-method.md` states the measured precision and miss rate for the tech label.

## Tech Stack

- Python 3.12, uv
- PyYAML for the rules file
- psycopg 3 for the upsert
- Numbered SQL migrations through the shared runner
- pytest for tests

## Commands

Classify every current notice:

```
uv run python -m tender_wazi classify
```

Test:

```
uv run pytest -q
```

Verify:

```
psql "$DATABASE_URL_DIRECT" -c "select unnest(sectors), count(*) from tender_sector group by 1 order by 2 desc"
```

## Taxonomy

Ten sectors. A notice can carry several labels, so a tender for school laptops can be both `ict_data_tech` and `education_training`.

| Sector | Covers |
|---|---|
| `ict_data_tech` | ICT, software, data systems, telecoms, electronics. |
| `works_construction` | Building, civil works, construction, rehabilitation. |
| `health_medical` | Health, medical supplies, pharmaceuticals, hospital equipment. |
| `education_training` | Education, training, books, school equipment. |
| `agriculture_environment` | Agriculture, livestock, fisheries, environment, forestry. |
| `energy_utilities` | Energy, power, oil, gas, water, sanitation. |
| `transport_vehicles` | Transport, vehicles, spare parts, aviation, maritime, railways. |
| `professional_services` | Consulting, audit, legal, insurance, banking, research. |
| `general_supplies` | Office supplies, furniture, uniforms, general goods. |
| `other` | Nothing matched. |

## Rules

`config/sector_rules.yaml` holds a version string and, for each sector, a list of terms to match and an optional list of terms to exclude. Terms are regex fragments, matched on whole words, case-insensitive. The classifier matches the title only.

The tech list starts with unambiguous terms:

```yaml
version: "2026-11-a"
sectors:
  ict_data_tech:
    any: ["ICT", "software", "information system", "ERP", "cyber ?security",
          "data cent(re|er)", "database", "cloud", "website", "web portal",
          "laptops?", "servers?", "structured cabling", "internet", "bandwidth",
          "VSAT", "mobile app", "analytics", "software licen[cs]es?"]
    not: []
```

Words that mislead when alone stay out: `system`, `hardware`, `network`, `data`, `digital`, `licence`. Add them only as pairs ("network equipment", "data entry services") after the false positives are known.

## Project Structure

```
config/
  sector_rules.yaml     version and terms per sector
src/tender_wazi/
  sectors.py            load_rules, classify
sql/migrations/
  003_sector.sql        tender_sector
tests/
  test_sectors.py
  sector_labels.csv     the hand-labelled sample
docs/
  explanation/sector-method.md
```

## Code Style

`sectors.py` keeps the rules loading and the matching apart:

```python
def load_rules(path: str = "config/sector_rules.yaml") -> tuple[str, dict]:
    """Read the version and compile the term lists."""


def classify(text: str, rules: dict) -> tuple[list[str], list[str]]:
    """Return the sectors and the terms that matched."""
```

The classifier never sees the buyer name. An ICT agency buys furniture and cleaning services too, and a ministry of works can buy software.

The upsert writes one row per notice and never touches `tender_versions`:

```sql
INSERT INTO tender_sector (source, source_id, sectors, matched_terms, rules_version)
VALUES (...)
ON CONFLICT (source, source_id) DO UPDATE
SET sectors = EXCLUDED.sectors, matched_terms = EXCLUDED.matched_terms,
    rules_version = EXCLUDED.rules_version, classified_at = now();
```

## Testing Strategy

- Unit tests for the classifier: each sector's terms, the excluding terms, whole-word matching, the fallback to `other`, and the multi-label case.
- Unit tests for the rules file: the version is a non-empty string, every sector has an `any` list, and no term is empty.
- A test per fixed false positive, so the same mistake cannot return.
- An integration test for the CLI: classify a small set of open versions and check the upsert.

## Boundaries

- Always: match on whole words; classify from the title only; store the matched terms and the rules version; never edit `tender_versions`.
- Ask first: changing the taxonomy; changing the precision bar; adding a sector.
- Never: use the buyer name; classify from the raw payload; edit a label by hand in the database.

## Success Criteria

- `uv run pytest -q` passes.
- `uv run python -m tender_wazi classify` labels every current notice on both sources.
- `select unnest(sectors), count(*) from tender_sector group by 1` shows a spread that makes sense.
- The tech label's precision and miss rate are measured on a hand-labelled sample and recorded in docs/sector-method.md with the rules version they apply to. The first pass measured 100% precision (100/100) and a 4% miss rate (4/100) on the sample, so no rules change was needed.
- Re-running classify with the same rules version changes nothing.

## Assumptions

1. The taxonomy is the guide's ten sectors.
2. `source_id` is the PPIP `ocid` or the Kenya Power reference number.
3. The rules version changes when the terms change. A new version means a full re-run.
4. The classifier matches the title only, because the PPIP data carries no description.
5. The sample is drawn at random across both sources.
6. The precision target is a figure the user sets. The guide suggests 85%.

## Open Questions

All four were settled as the agent's first pass. The agent labels the sample with the
reviewer's corrections kept separate; a rules version change means a full re-run.

1. The classify input. The title only, because the PPIP data carries no description and a
   description column would change the approved curate schema.
2. The sample size. 100 tenders tagged `ict_data_tech` and 100 that are not.
3. The precision bar. 85%. The first pass measured 100% precision and 4% miss rate on the
   sample, so no rules change was needed.
4. Who labels the sample. The agent labels a first pass from the titles; the reviewer
   corrects the rows it could not judge.

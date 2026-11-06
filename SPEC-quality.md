# Spec: quality

## Objective

The pipeline tells you when data is wrong or a source has quietly changed, and
does not load bad data without saying so. Row checks, table checks and drift
alerts all land in `quality_runs` or `rejects`; nothing bad is dropped silently.

## Responsibility

- Row validation: required fields present, dates parse, amounts non-negative,
  currency allowed. Rejected rows go to `rejects` with a reason and the raw
  reference.
- Table checks after each load: null rates, duplicate open versions, outliers,
  sector spread. Each run stores one row in `quality_runs`.
- Volume drift: new or updated notices per source per day, compared with the
  trailing 30 days.
- Schema drift for HTML: share of pages where each required selector matched.
- A `source_health` view (latest run, last successful fetch, counts) readable
  from the read-only role.

## Tech stack

- Python 3.12, uv
- Pydantic (v2) for row validation, psycopg 3 for the checks
- Numbered SQL migrations through the shared runner
- pytest for tests

## Commands

```
uv run python -m tender_wazi check
uv run pytest -q
psql "$DATABASE_URL_DIRECT" -c "select run_id, source, ok, message from quality_runs order by run_at desc limit 5"
```

## Project structure

```
src/tender_wazi/
  checks.py           row validation, table checks, volume_alert, record functions
sql/migrations/
  004_quality.sql     quality_runs, rejects, source_health
  005_quality.sql     portal_b_details
tests/
  test_checks.py
```

## Code style

Row checks are a Pydantic model per source. A row that fails goes to `rejects`
with the reason and the raw reference, and the run records an `ok=false`
`quality_runs` row. Table checks collect their results into `quality_runs` too.

The volume alert reuses the guide's function: a trailing 30-day window, flag a
fall more than two standard deviations below the 30-day mean.

```python
# src/tender_wazi/checks.py
def volume_alert(daily, window: int = 30, k: float = 2.0) -> bool:
    """daily has columns d (date) and n (count), sorted by d."""
    ...
```

Schema drift for HTML records, per source, how many pages each required
selector matched. If a required field matches on less than 90% of pages, the
run fails and alerts.

The checks are separate from the load: a run imports the data, then calls
`checks.record_all(conn, source, results)`, which writes `quality_runs` and
`rejects`. A run that fails loudly leaves bad data on disk and notifies.

## Testing strategy

- Unit tests for each Pydantic model: required fields, negative amounts, unknown
  currency, unreadable dates.
- Unit tests for `volume_alert`: a low volume day returns True; a normal day returns
  False.
- Unit tests for `check_schema_drift`: a fixture where a required field is missing
  fails the run; a normal fixture passes.
- Integration tests for `quality_runs` and `rejects`: a load, a check, and the run
  row is present.
- Planned fixtures remain open: a PPIP row with an empty `awards` array, a missing
  buyer identifier, a bad supplier identifier, and a `parties` entry without a name.
  They will be added with the PPIP quality fixtures in the next module pass.

## Boundaries

- Always: record rejects; record a `quality_runs` row; fail the run loudly.
- Ask first: changing the quality schema; changing the thresholds; adding a
  source.
- Never: drop a rejected row; delete a quality run.

## Success criteria

- `uv run pytest -q` passes.
- `uv run python -m tender_wazi check` runs all checks and exits non-zero when
  any check fails.
- `quality_runs` has one row per load with the check results.
- `rejects` captures every bad row with a reason and a raw reference.
- The `source_health` view is readable by the read-only role.
- The two checkpoints hold: a fixture with a removed selector fails a run; a
  fake low-volume day makes `volume_alert` return True.

## Assumptions

1. Row checks use Pydantic (added as a dependency).
2. `quality_runs` keeps one row per load per source.
3. The thresholds: null rate above 20% fails; schema match below 90% fails.
4. Volume drift uses a 30-day window and two standard deviations.
5. `source_health` is a view over `quality_runs` and `raw_manifest` in the
   public schema, readable by the local read-only role.

## Open questions

1. `source_health` is a view in the public schema for the MVP. The guide puts
   the API views in a separate schema once the API exists.
2. The schema-drift check currently covers the Kenya Power HTML field set; the
   PPIP layer has no HTML selectors to drift.
3. Outliers are flagged but kept; the threshold is the 99th percentile of
   `value_amount`.

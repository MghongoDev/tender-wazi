# Quality

The pipeline tells you when data is wrong or a source goes quiet, and does not load
bad data silently.

## Responsibility

- Row validation: required fields present, dates parse, amounts non-negative,
  currency allowed. Rejected rows go to `rejects` with a reason and raw reference.
- Table checks after each load: null rates, duplicate open versions, outliers,
  sector spread. One `quality_runs` row per load.
- Volume drift: new or updated notices per source per day, compared with the trailing
  thirty days. A fall of more than two standard deviations below the mean flags a
  quiet source.
- Schema drift for HTML: share of pages where each required selector matched.
- A `source_health` view: the latest quality run, whether it was ok, and how many
  raw payloads each source has fetched.

## Commands

```
uv run python -m tender_wazi check
uv run pytest -q
psql "$DATABASE_URL_DIRECT" -c "select source, ok, message from quality_runs order by run_at desc"
```

## Code style

Row checks are a Pydantic model per source; a failed row becomes a `rejects` row with
a reason. Table checks collect into `quality_runs`.

The volume alert compares the last day's count with the mean of the trailing window
(when there are at least two prior days): a fall of more than two standard
deviations below the mean flags a quiet source.

HTML schema drift records how many pages each required selector matched; a field
matching on under 90% of pages fails the run. A run that fails any check exits
non-zero, so the daily workflow notifies without extra tooling.

## Testing strategy

- Unit tests for each Pydantic model: required fields, dates, negative amounts,
  unknown currency.
- Unit tests for `volume_alert`: a low-volume day returns True; a normal day returns
  False.
- Unit tests for `check_schema_drift`: a fixture with a removed selector fails;
  a normal fixture passes.
- Integration tests for `quality_runs` and `rejects`: a load, a check, and the run
  row is present.
- Fixtures: a PPIP row missing a title, a negative amount, an unknown currency, and
  an unreadable date.

## Boundaries

- Always: record rejects; record a `quality_runs` row; fail the run loudly.
- Ask first: changing the quality schema; changing the thresholds.
- Never: drop a rejected row; delete a quality run.

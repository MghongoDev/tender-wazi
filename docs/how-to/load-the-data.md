# Load the data

## Prerequisites

- `.env` with `DATABASE_URL_DIRECT`, `RAW_BUCKET` and the storage keys.
- The migrations applied: `uv run python -m tender_wazi migrate`.

## Load one year of PPIP

```
uv run python -m tender_wazi run --source ppip --year 2025
```

This fetches the year, saves the raw payload, parses it, stages it, normalizes it and versions it.

## Load Kenya Power

```
uv run python -m tender_wazi run --source portal_b
```

This reads page 1 of the listing and each detail page.

## Verify

```
psql "$DATABASE_URL_DIRECT" -c "select source, count(*) from tender_versions where valid_to is null group by 1"
```

## Re-run

A re-run of an unchanged source adds no versions. It updates `tender_seen.last_seen_at`.

## Change one notice

To see versioning work, change a title in a saved raw payload and re-run the load. The notice gets a new version. The old version closes at the same instant the new one opens.

## What to do when a load fails

The load runs in one transaction. A failure rolls back, so the curated tables keep their previous state. The raw payload is already saved, so the next run starts from the raw layer.

## Run the quality checks

After each load the quality checks run and record in `quality_runs`. A run that fails any check exits non-zero and notifies.

```bash
uv run python -m tender_wazi check
```

The checks cover null rates per key field, duplicate open versions, value outliers,
sector spread, volume drift and (for the HTML source) schema drift. Rejects are
captures in `rejects`, never dropped.

## Source health

The `source_health` view summarises each source's latest run, whether it was ok, and
the raw fetch counts.

```bash
psql "$DATABASE_URL_DIRECT" -c "select * from source_health"
```

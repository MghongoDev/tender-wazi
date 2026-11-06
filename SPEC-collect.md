# Spec: collect

## Objective

Fetch public tender notices from PPIP (OCDS) and Kenya Power's tender listing, save every raw payload to object storage, record each fetch in raw_manifest, and keep the source record in docs/reference/sources.md.

Success looks like: `python -m tender_wazi run --source ppip --year 2025` saves the raw file and its manifest row; `python -m tender_wazi run --source portal_b` saves raw HTML and manifest rows; a second run of an unchanged source adds no duplicate raw rows; the parsers pass their fixture tests.

## Tech Stack

- Python 3.12, uv
- httpx for HTTP
- boto3 for the raw bucket (Neon Object Storage, S3-compatible)
- psycopg 3 for the manifest
- pytest for tests

## Commands

Setup:

```
uv sync
```

Migrate:

```
uv run python -m tender_wazi migrate
```

Run:

```
uv run python -m tender_wazi run --source ppip --year 2025
uv run python -m tender_wazi run --source portal_b --max-pages 3
```

Test:

```
uv run pytest -q
```

Verify a load:

```
psql "$DATABASE_URL_DIRECT" -c "select source, count(*) from raw_manifest group by 1"
```

## Project Structure

```
src/tender_wazi/
  __init__.py
  http.py          polite client
  raw.py           save_raw, manifest
  migrate.py       numbered SQL runner
  cli.py           python -m tender_wazi run --source ...
  sources/
    __init__.py
    ppip.py        OCDS reader
    portal_b.py    Kenya Power scraper
sql/migrations/
  001_init.sql     raw_manifest
tests/
  fixtures/
    ppip_2025_sample.jsonl
    kplc_tender_listing.html
    kplc_tender_detail.html
  test_http.py
  test_raw.py
  test_ppip.py
  test_portal_b.py
docs/
  reference/sources.md
```

## Code Style

- Parsers are pure functions: `parse_detail(html: str) -> dict`. Tests feed them saved fixtures.
- Keep the CSS selectors at the top of portal_b.py.
- Keep the original string next to the parsed value (`closing_date_raw` beside `closing_at`), so a parsing mistake stays visible.
- Keep the raw layer immutable. Collect fetches bytes and saves them; it never parses.

## Testing Strategy

- Unit tests with pytest for http.py, raw.py, ppip.py and portal_b.py.
- TDD: write the failing test, run it, implement, run it, commit.
- Fixtures: one per source, plus a broken-page test for the scraper.
- Integration: run the CLI against Neon dev, then check raw_manifest and the bucket.

## Boundaries

- Always: save the raw bytes before parsing; keep the raw layer immutable; use the polite client for every request.
- Ask first: adding a source; changing the bucket or the region; scraping a source whose terms are unclear.
- Never: parse in the collect stage and discard the raw bytes; commit raw payloads to git; print a connection string.

## Success Criteria

- `uv run pytest -q` passes.
- `uv run python -m tender_wazi migrate` creates raw_manifest on dev.
- `uv run python -m tender_wazi run --source ppip --year 2025` saves the raw file and one manifest row.
- `uv run python -m tender_wazi run --source portal_b` fetches page 1 of the Kenya Power listing and its detail pages, saves raw HTML and manifest rows, and dedupes by reference. Request gaps are at least 2 seconds. The Livewire pagination beyond page 1 is a documented limitation.
- A second run of an unchanged source adds no duplicate raw rows.
- docs/reference/sources.md records both sources with the date checked.

## Decisions

1. Kenya Power pagination: page 1 only for the MVP. Page 2 and beyond use Laravel Livewire (POST /livewire/update with a CSRF token and a component snapshot). A scripted update returned 419 and 500 in testing, so it is deferred.
2. e-GP: deferred until after the MVP. It is the new system of record but a JavaScript app that needs its API or a headless browser.
3. Migration runner: shared. collect bootstraps it (src/tender_wazi/migrate.py) and owns raw_manifest; curate's migrations use the same runner.

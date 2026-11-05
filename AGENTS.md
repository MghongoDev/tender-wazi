# Tender-wazi

## Tech stack

- Python 3.12, uv
- httpx, boto3, psycopg 3, beautifulsoup4, lxml
- Neon Postgres and Neon Object Storage
- pytest

## Commands

- Setup: `uv sync`
- Test: `uv run pytest -q`
- Migrate: `uv run python -m tender_wazi migrate`
- Run: `uv run python -m tender_wazi run --source ppip --year 2025`

## Conventions

- Parsers are pure functions. Tests feed them saved fixtures.
- Save the raw bytes before parsing. The raw layer is immutable.
- Keep the original string next to the parsed value.
- Tests live in tests/ and use the fixtures in tests/fixtures/.

## Boundaries

- Never commit .env, neon.txt or raw payloads.
- Never print a connection string.
- Ask before adding a source or changing the bucket.
